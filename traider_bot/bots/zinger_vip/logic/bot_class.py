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
        self.position_info = None  # dict
        self.current_price = None  # str

        self.percent = Decimal(0.1)
        self.order_count = 5
        self.order_list = []

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

        self.position_info = get_position_inform(self.bot)

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
        if self.position_info:
            order_list = []
            for psn in self.position_info:
                psn_side = psn['side']
                psn_qty = Decimal(psn['qty'])
                psn_price = Decimal(psn['entryPrice'])
                psn_cost = psn_price * psn_qty

                if psn_side == 'LONG':
                    long_orders = {}
                    for number_order in range(self.order_count):
                        order_price = psn_price * (1 + self.percent)
                        order_cost = order_price * psn_qty
                        cost_diff = abs(order_cost - psn_cost)
                        coin_sold_count = cost_diff / order_price
                        qty_after_sold = psn_qty - coin_sold_count

                        long_orders[number_order] = {
                            'order_price': order_price,
                            'order_cost': order_cost,
                            'cost_diff': cost_diff,
                            'qty_after_sold': qty_after_sold,
                            'coin_sold_count': coin_sold_count,
                        }

                        psn_qty = qty_after_sold
                        psn_price = order_price
                        psn_cost = psn_price * psn_qty

                    self.order_list.append(long_orders)

                else:
                    short_orders = {}
                    for number_order in range(self.order_count):
                        order_price = psn_price / (1 + self.percent)
                        order_cost = order_price * psn_qty
                        cost_after_reduction = order_cost - (order_cost * self.percent)
                        qty_after_sold = cost_after_reduction / order_price
                        coin_sold_count = psn_qty - qty_after_sold

                        short_orders[number_order] = {
                            'order_price': order_price,
                            'order_cost': order_cost,
                            'cost_after_reduction': cost_after_reduction,
                            'qty_after_sold': qty_after_sold,
                            'coin_sold_count': coin_sold_count,
                        }

                        psn_qty = qty_after_sold
                        psn_price = order_price

                    self.order_list.append(short_orders)

