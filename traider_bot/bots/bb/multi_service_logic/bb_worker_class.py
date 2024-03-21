import threading
from decimal import Decimal

from api_2.api_aggregator import change_position_mode, set_leverage, cancel_all_orders, place_order, get_position_inform
from bots.bb.multi_service_logic.avg_logic import BBAutoAverage
from bots.bb_class import BollingerBands


class WorkBollingerBandsClass:
    def __init__(self, bot):
        self.bot = bot
        self.symbol = bot.symbol.name
        self.bb = BollingerBands(bot)
        self.avg_obj = BBAutoAverage(bot, self.bb)
        self.have_psn = False
        self.ml_filled = False
        self.ml_order_id = None
        self.position_info = None

        self.locker_1 = threading.Lock()
        self.avg_locker = threading.Lock()

    def preparatory_actions(self):
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
        if self.bot.side == 'FB':
            place_order(self.bot, side='Buy', order_type='Limit', price=self.bb.bl)
            place_order(self.bot, side='Sell', order_type='Limit', price=self.bb.tl)
        elif self.bot.side == 'Buy':
            place_order(self.bot, side='Buy', order_type='Limit', price=self.bb.bl)
        elif self.bot.side == 'Sell':
            place_order(self.bot, side='Sell', order_type='Limit', price=self.bb.tl)

    def replace_closing_orders(self):
        cancel_all_orders(self.bot)
        position_side = self.position_info['side']

        side, price = ('Sell', self.bb.tl) if position_side == 'LONG' else ('Buy', self.bb.bl)
        price = self.price_check(price, 2)

        if self.bot.take_on_ml and not self.ml_filled:
            psn_qty = Decimal(self.position_info['qty'])
            ml_take_price = self.price_check(self.bb.ml, 1)
            ml_take_qty = Decimal(str(psn_qty * self.bot.take_on_ml_percent / 100)).quantize(
                Decimal(self.bot.symbol.minOrderQty))

            response = place_order(self.bot, side=side, position_side=position_side, order_type='Limit',
                                   qty=ml_take_qty, price=ml_take_price)
            self.ml_order_id = response['orderId']

            main_take_qty = psn_qty - ml_take_qty
        else:
            main_take_qty = Decimal(self.position_info['qty'])

        place_order(self.bot, side=side, position_side=position_side, order_type='Limit', qty=main_take_qty,
                    price=price)

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
