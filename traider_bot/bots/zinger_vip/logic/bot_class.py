import threading
import time
from decimal import Decimal

from api_2.api_aggregator import change_position_mode, set_leverage, cancel_all_orders, place_order, \
    get_position_inform, place_batch_order
from bots.bb.multi_service_logic.avg_logic import BBAutoAverage
from bots.bb_class import BollingerBands


class WorkZingerVipClass:
    def __init__(self, bot):
        self.bot = bot
        self.symbol = bot.symbol
        self.bb = BollingerBands(bot)
        self.position_info = {
            'LONG': {
                'side': 'LONG',
                'qty': 0,
                'entryPrice': 0,
            }, 'SHORT': {
                'side': 'SHORT',
                'qty': 0,
                'entryPrice': 0,
            }
        }  # dict
        self.current_price = None  # str

        self.percent = Decimal(0.1)
        self.order_count = 10
        self.order_list = {'LONG': {}, 'SHORT': {}}

        self.locker_1 = threading.Lock()

    def preparatory_actions(self):
        try:
            change_position_mode(self.bot)
        except:
            pass
        try:
            set_leverage(self.bot)
        except:
            pass

        # self.position_info = get_position_inform(self.bot)

    def open_psns_with_start(self):
        while not self.current_price:
            time.sleep(0.1)

        long_order = {
            'symbol': self.symbol.name,
            'side': 'BUY',
            'positionSide': 'LONG',
            'type': 'MARKET',
            'price': self.current_price,
        }
        short_order = {
            'symbol': self.symbol.name,
            'side': 'SELL',
            'positionSide': 'SHORT',
            'type': 'MARKET',
            'price': self.current_price,
        }
        place_batch_order(self.bot, order_list=[long_order, short_order])

    def place_reduction_orders(self):
        for psn_side, psn in self.position_info.items():
            if psn['qty']:
                psn_qty = Decimal(psn['qty'])
                psn_price = Decimal(psn['entryPrice'])
                psn_cost = psn_price * psn_qty
                print(psn_side)

                if psn_side == 'LONG':
                    for number_order in range(self.order_count):
                        order_price = psn_price * (1 + self.percent)
                        order_cost = order_price * psn_qty
                        cost_diff = abs(order_cost - psn_cost)
                        coin_sold_count = cost_diff / order_price
                        qty_after_sold = psn_qty - coin_sold_count

                        order = {
                            'order_price': round(order_price, 10),
                            'order_cost': round(order_cost, 10),
                            'cost_diff': round(cost_diff, 10),
                            'qty_after_sold': round(qty_after_sold, 10),
                            'coin_sold_count': round(coin_sold_count, 10),
                        }
                        self.order_list['LONG'][number_order] = order

                        psn_qty = qty_after_sold
                        psn_price = order_price
                        psn_cost = psn_price * psn_qty

                elif psn_side == 'SHORT':
                    for number_order in range(self.order_count):
                        order_price = psn_price / (1 + self.percent)
                        # order_price = psn_price - (psn_price * self.percent)
                        order_cost = order_price * psn_qty
                        cost_after_reduction = order_cost / (1 + self.percent)
                        # cost_after_reduction = order_cost - (order_cost * self.percent)
                        qty_after_sold = cost_after_reduction / order_price
                        coin_sold_count = psn_qty - qty_after_sold

                        order = {
                            'order_price': round(order_price, 10),
                            'order_cost': round(order_cost, 10),
                            'cost_after_reduction': round(cost_after_reduction, 10),
                            'qty_after_sold': round(qty_after_sold, 10),
                            'coin_sold_count': round(coin_sold_count, 10),
                        }
                        self.order_list['SHORT'][number_order] = order

                        psn_qty = qty_after_sold
                        psn_price = order_price

        for orders in self.order_list.values():
            print()
            for order in orders.values():
                print(order)
            print()
