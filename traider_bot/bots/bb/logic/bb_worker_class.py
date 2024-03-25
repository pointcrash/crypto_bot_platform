import logging
import threading
import time
from decimal import Decimal

from api_2.api_aggregator import change_position_mode, set_leverage, cancel_all_orders, place_order, \
    get_position_inform, place_conditional_order
from bots.bb.logic.avg_logic import BBAutoAverage
from bots.bb_class import BollingerBands


class WorkBollingerBandsClass:
    def __init__(self, bot):
        self.bot = bot
        self.symbol = bot.symbol.name
        self.bb = BollingerBands(bot)
        self.avg_obj = BBAutoAverage(bot, self.bb)
        self.current_price = None
        self.have_psn = False
        self.ml_filled = False
        self.ml_order_id = None
        self.main_order_id = None
        self.position_info = None

        self.locker_1 = threading.Lock()
        self.avg_locker = threading.Lock()

    def preparatory_actions(self):
        logging.basicConfig(level=logging.DEBUG)
        try:
            change_position_mode(self.bot)
        except:
            pass
        try:
            set_leverage(self.bot)
        except:
            pass

        not_null_psn_list = list(psn for psn in get_position_inform(self.bot) if float(psn['qty']) != 0)

        if len(not_null_psn_list) > 1:
            raise Exception('More than one position')
        elif len(not_null_psn_list) == 1:
            self.have_psn = True
            self.position_info = not_null_psn_list[0]
            self.avg_obj.update_psn_info(self.position_info)
            self.replace_closing_orders()
        else:
            self.replace_opening_orders()

    def replace_opening_orders(self):
        cancel_all_orders(self.bot)
        side = self.bot.bb.side
        amount_usdt = self.bot.amount_long

        while not self.current_price:
            time.sleep(0.5)

        if side == 'FB' or side == 'LONG':
            if self.current_price <= self.bb.bl:
                return place_order(self.bot, side='BUY', order_type='MARKET', price=self.current_price,
                                   amount_usdt=amount_usdt)
            place_conditional_order(self.bot, side='BUY', position_side='LONG', trigger_price=self.bb.bl,
                                    trigger_direction=2, amount_usdt=amount_usdt)
        if side == 'FB' or side == 'SHORT':
            if self.current_price >= self.bb.tl:
                return place_order(self.bot, side='SELL', order_type='MARKET', price=self.current_price,
                                   amount_usdt=amount_usdt)
            place_conditional_order(self.bot, side='SELL', position_side='SHORT', trigger_price=self.bb.tl,
                                    trigger_direction=1, amount_usdt=amount_usdt)

    def replace_closing_orders(self):
        cancel_all_orders(self.bot)
        position_side = self.position_info['side']
        psn_qty = Decimal(self.position_info['qty'])

        side, price, td = ('SELL', self.bb.tl, 1) if position_side == 'LONG' else ('BUY', self.bb.bl, 2)
        price = self.price_check(price, 2)

        if self.bot.bb.take_on_ml and not self.ml_filled and psn_qty > Decimal(self.bot.symbol.minOrderQty):
            ml_take_price = self.price_check(self.bb.ml, 1)
            ml_take_qty = Decimal(str(psn_qty * self.bot.bb.take_on_ml_percent / 100)).quantize(
                Decimal(self.bot.symbol.minOrderQty))

            # response = place_order(self.bot, side=side, position_side=position_side, order_type='Limit',
            #                        qty=ml_take_qty, price=ml_take_price)
            response = place_conditional_order(self.bot, side=side, position_side=position_side,
                                               trigger_price=ml_take_price, trigger_direction=td, qty=ml_take_qty)
            # logging.debug(response)
            self.ml_order_id = response['orderId']

            main_take_qty = psn_qty - ml_take_qty
        else:
            main_take_qty = Decimal(self.position_info['qty'])

        # response = place_order(self.bot, side=side, position_side=position_side, order_type='Limit', qty=main_take_qty,
        #                        price=price)
        response = place_conditional_order(self.bot, side=side, position_side=position_side,
                                           trigger_price=price, trigger_direction=td, qty=main_take_qty)
        # logging.debug(response)
        self.main_order_id = response['orderId']

    def price_check(self, price, take_number):
        psn_side = self.position_info['side']
        psn_price = Decimal(self.position_info['entryPrice'])
        tick_size = Decimal(self.bot.symbol.tickSize)
        take_distance = tick_size * 3 if take_number == 1 else tick_size * 6

        if psn_side == 'LONG':
            if price < psn_price:
                return psn_price + take_distance
            return price
        elif psn_side == 'SHORT':
            if price > psn_price:
                return psn_price - take_distance
            return price
