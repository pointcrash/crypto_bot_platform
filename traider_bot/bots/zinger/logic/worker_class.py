import threading
import time
from decimal import Decimal, ROUND_HALF_UP

from api_2.api_aggregator import change_position_mode, set_leverage, place_order, get_position_inform
from api_2.custom_logging_api import custom_logging


class WorkZingerClass:
    def __init__(self, bot):
        self.bot = bot
        self.symbol = bot.symbol.name
        self.current_price = None
        self.open_order_id_list = dict()
        self.tp_order_id_list = dict()
        self.end_order_id_list = dict()
        self.position_info = dict()
        self.realizedPnl = 0
        self.unrealizedPnl = dict()
        self.nipple_side = ''
        self.income = self.calc_income()

        self.psn_locker = threading.Lock()
        self.order_locker = threading.Lock()

    def calc_income(self):
        return (self.bot.amount_long + self.bot.amount_short) * (self.bot.zinger.income_percent / 100)

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
            with self.order_locker:
                for side in ['BUY', 'SELL']:
                    psn_side = 'LONG' if side == 'BUY' else 'SHORT'
                    order_id = self.start_open_psn(side)
                    self.open_order_id_list[psn_side] = order_id

    def check_opened_psn(self):
        psn_data = get_position_inform(self.bot)
        if float(psn_data[0]['qty']) != 0 and float(psn_data[1]['qty']) != 0:
            for psn_side in ['LONG', 'SHORT']:
                self.position_info[psn_side] = psn_data[0] if psn_data[0]['side'] == psn_side else psn_data[1]
                self.position_info[psn_side]['entryPrice'] = abs(Decimal(self.position_info[psn_side]['entryPrice']))
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
        if psn_side == 'LONG':
            side = 'SELL'
            percent = self.bot.zinger.tp_pnl_percent_long
            order_price = psn_price + (psn_price * percent / self.bot.leverage / 100)
        elif psn_side == 'SHORT':
            side = 'BUY'
            percent = self.bot.zinger.tp_pnl_percent_short
            order_price = psn_price - (psn_price * percent / self.bot.leverage / 100)
        else:
            raise Exception(f'Not correct side position_info: {psn_side}')

        order_price = round(order_price, int(self.bot.symbol.priceScale))
        response = place_order(self.bot, side=side, position_side=psn_side, order_type='LIMIT', price=order_price,
                               qty=psn_qty)
        self.tp_order_id_list[psn_side] = response['orderId']
        self.unrealizedPnl[psn_side] = abs(psn_price - order_price) * psn_qty

    def place_second_open_order(self, psn_side, psn_qty):
        if psn_side == 'LONG':
            side = 'BUY'
            percent = self.bot.zinger.tp_pnl_percent_long
        elif psn_side == 'SHORT':
            side = 'SELL'
            percent = self.bot.zinger.tp_pnl_percent_short
        else:
            raise Exception(f'Not correct side position_info: {psn_side}')

        qty = psn_qty - (psn_qty * percent / self.bot.leverage / 100)
        qty = qty.quantize(Decimal(self.bot.symbol.qtyStep), rounding=ROUND_HALF_UP)
        response = place_order(self.bot, side=side, order_type='MARKET', price=self.current_price, qty=qty)
        self.open_order_id_list[psn_side] = response['orderId']
        print(self.open_order_id_list)

    def nipple(self):
        if not self.nipple_side:
            return

        if self.nipple_side == 'LONG':
            pass
        if self.nipple_side == 'SHORT':
            pass

    def calc_pnl(self):
        current_pnl = self.realizedPnl
        for psn_side, psn in self.position_info.items():
            if psn_side == 'LONG':
                current_pnl += (self.current_price - psn['entryPrice']) * psn['qty']
            elif psn_side == 'SHORT':
                current_pnl += (psn['entryPrice'] - self.current_price) * psn['qty']
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
