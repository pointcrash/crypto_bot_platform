import copy
import threading
import time

from django.core.cache import cache
from decimal import Decimal, ROUND_HALF_UP

from api_2.api_aggregator import change_position_mode, set_leverage, place_order, get_position_inform
from api_2.custom_logging_api import custom_logging


class WorkZingerClassMarket:
    def __init__(self, bot):
        self.bot = bot
        self.zinger = bot.zinger
        self.symbol = bot.symbol.name
        self.tick_size = Decimal(bot.symbol.tickSize)
        self.current_price = None
        self.open_order_id_list = dict()
        self.nipple_data_list = dict()
        self.tp_order_id_list = dict()
        self.end_order_id_list = dict()
        self.position_info = dict()
        self.unrealizedPnl = dict()
        self.realizedPnl = self.zinger.realized_pnl
        self.required_income = self.calc_required_income()

        self.multiplication_factor = dict()
        self.tp_income_long = bot.amount_long * bot.zinger.tp_pnl_percent_long / 100
        self.tp_income_short = bot.amount_short * bot.zinger.tp_pnl_percent_short / 100

        self.psn_locker = threading.Lock()
        self.order_locker = threading.Lock()

    def cached_data(self, key, value):
        cache.set(f'bot{self.bot.id}_{key}', str(value), timeout=3600)

    def calc_required_income(self):
        return (self.bot.amount_long + self.bot.amount_short) * (self.zinger.income_percent / 100)

    def preparatory_actions(self):
        try:
            change_position_mode(self.bot)
        except:
            pass
        try:
            set_leverage(self.bot)
        except:
            pass
        if not self.check_opened_psn():
            for side in ['BUY', 'SELL']:
                with self.order_locker:
                    psn_side = 'LONG' if side == 'BUY' else 'SHORT'
                    order_id = self.start_open_psn(side)
                    self.open_order_id_list[psn_side] = order_id
        else:
            for psn_side, psn in self.position_info.items():
                self.place_tp_orders(psn_side, Decimal(psn['entryPrice']), Decimal(psn['qty']))

    def check_opened_psn(self):
        psn_data = get_position_inform(self.bot)
        if float(psn_data[0]['qty']) != 0 and float(psn_data[1]['qty']) != 0:
            for psn_side in ['LONG', 'SHORT']:
                self.position_info[psn_side] = psn_data[0] if psn_data[0]['side'] == psn_side else psn_data[1]
                self.position_info[psn_side]['entryPrice'] = abs(Decimal(self.position_info[psn_side]['entryPrice']))
                self.position_info[psn_side]['qty'] = abs(Decimal(self.position_info[psn_side]['qty']))
            return True
        elif float(psn_data[0]['qty']) != 0 or float(psn_data[1]['qty']) != 0:
            raise Exception(f'Одна из позиций не равна 0')
        else:
            return False

    def start_open_psn(self, side):
        while not self.current_price:
            time.sleep(0.1)

        amount_usdt = self.bot.amount_long if side == 'BUY' else self.bot.amount_short
        response = place_order(self.bot, side=side, order_type='MARKET', price=self.current_price,
                               amount_usdt=amount_usdt)
        return response['orderId']

    def place_tp_orders(self, psn_side, psn_price, psn_qty):
        psn_cost = psn_qty * psn_price
        if psn_side == 'LONG':
            side = 'SELL'
            order_price = (psn_cost + self.tp_income_long) / psn_qty
        elif psn_side == 'SHORT':
            side = 'BUY'
            order_price = abs((-psn_cost + self.tp_income_short) / psn_qty)
        else:
            raise Exception(f'Not correct side position_info: {psn_side}')

        # order_price = order_price.quantize(Decimal(self.bot.symbol.tickSize), rounding=ROUND_HALF_UP)
        order_price = round(order_price, int(self.bot.symbol.priceScale))

        prices = [psn_price, order_price]
        self.multiplication_factor[psn_side] = max(prices) / min(prices)
        response = place_order(self.bot, side=side, position_side=psn_side, order_type='LIMIT', price=order_price,
                               qty=psn_qty)
        self.tp_order_id_list[psn_side] = response['orderId']
        self.unrealizedPnl[psn_side] = abs(psn_price - order_price) * psn_qty

        self.cached_data(key='unrealizedPnl', value=self.unrealizedPnl)
        self.cached_data(key='multFactor', value=self.multiplication_factor)

    def get_side_and_qty_for_second_orders(self, psn_side, psn_qty):
        if psn_side == 'LONG':
            side = 'BUY'
            percent = self.zinger.tp_pnl_percent_long
        elif psn_side == 'SHORT':
            side = 'SELL'
            percent = self.zinger.tp_pnl_percent_short
        else:
            raise Exception(f'Not correct side position_info: {psn_side}')

        qty = psn_qty / self.multiplication_factor
        # qty = psn_qty - (psn_qty * percent / self.bot.leverage / 100)
        qty = qty.quantize(Decimal(self.bot.symbol.qtyStep), rounding=ROUND_HALF_UP)
        if qty == psn_qty and qty > Decimal(self.bot.symbol.minOrderQty):
            qty -= Decimal(self.bot.symbol.qtyStep)
        return side, qty

    def calc_second_open_order_price_by_nipple(self, psn_side, psn_qty, price):
        order_price = price + self.zinger.qty_steps * self.tick_size
        self.cached_data(key=f'2OpOrPr{psn_side}', value=order_price)

        self.nipple_data_list[psn_side] = {'psn_side': psn_side, 'psn_qty': psn_qty, 'price': order_price}

    def place_second_open_order(self, psn_side, psn_qty):
        side, qty = self.get_side_and_qty_for_second_orders(psn_side, psn_qty)

        with self.order_locker:
            response = place_order(self.bot, side=side, order_type='MARKET', price=self.current_price, qty=qty)
            self.open_order_id_list[psn_side] = response['orderId']

    def nipple(self):
        if not self.nipple_data_list:
            return

        if self.nipple_data_list.get('LONG'):
            order_data = self.nipple_data_list['LONG']
            if order_data['price'] - self.current_price > self.zinger.qty_steps * self.tick_size:
                self.nipple_data_list['LONG']['price'] = self.current_price + self.zinger.qty_steps * self.tick_size
                self.cached_data(key=f'2OpOrPrLONG', value=self.nipple_data_list['LONG']['price'])

            elif self.current_price >= order_data['price']:
                self.place_second_open_order(order_data['psn_side'], order_data['psn_qty'])

        if self.nipple_data_list.get('SHORT'):
            order_data = self.nipple_data_list['SHORT']
            if self.current_price - order_data['price'] > self.zinger.qty_steps * self.tick_size:
                self.nipple_data_list['SHORT']['price'] = self.current_price - self.zinger.qty_steps * self.tick_size
                self.cached_data(key=f'2OpOrPrSHORT', value=self.nipple_data_list['SHORT']['price'])

            elif self.current_price <= order_data['price']:
                self.place_second_open_order(order_data['psn_side'], order_data['psn_qty'])

    def calc_pnl(self):
        current_pnl = copy.copy(self.realizedPnl)
        for psn_side, psn in self.position_info.items():
            if psn_side == 'LONG':
                pnl_long = (self.current_price - psn['entryPrice']) * psn['qty']
                # current_pnl += (self.current_price - psn['entryPrice']) * psn['qty']
                current_pnl += pnl_long
                self.cached_data(key=f'pnlLong', value=pnl_long)

            elif psn_side == 'SHORT':
                pnl_short = (psn['entryPrice'] - self.current_price) * psn['qty']
                # current_pnl += (psn['entryPrice'] - self.current_price) * psn['qty']
                current_pnl += pnl_short
                self.cached_data(key=f'pnlShort', value=pnl_short)
        self.cached_data(key=f'currentPnl', value=current_pnl)
        return current_pnl

    def end_cycle(self, pnl):
        response = place_order(self.bot, side='SELL', position_side='LONG', order_type='MARKET',
                               price=self.current_price, qty=self.position_info['LONG']['qty'])
        self.end_order_id_list['LONG'] = response['orderId']

        response = place_order(self.bot, side='BUY', position_side='SHORT', order_type='MARKET',
                               price=self.current_price, qty=self.position_info['SHORT']['qty'])
        self.end_order_id_list['SHORT'] = response['orderId']
        custom_logging(self.bot, f'Конец цикла. Расчетный PNL: {pnl}')

        self.bot.is_active = False
        self.bot.save()

    def update_realized_pnl(self, psn_side):
        self.realizedPnl += self.unrealizedPnl[psn_side]
        self.cached_data(key=f'realizedPnl', value=self.realizedPnl)
        self.zinger.realized_pnl = self.realizedPnl
        self.zinger.save()
