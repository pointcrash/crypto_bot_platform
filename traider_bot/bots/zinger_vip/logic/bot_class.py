import threading
import time
from decimal import Decimal, ROUND_DOWN, ROUND_UP

from api_2.api_aggregator import change_position_mode, set_leverage, cancel_all_orders, place_order, \
    get_position_inform, place_batch_order
from bots.bb.multi_service_logic.avg_logic import BBAutoAverage
from bots.bb_class import BollingerBands
from bots.zinger_vip.logic.reduce_order_classes import ShortReduceOrder, LongReduceOrder


class WorkZingerVipClass:
    def __init__(self, bot):
        self.bot = bot
        self.symbol = bot.symbol
        self.symbol_name = bot.symbol.name
        self.bb = BollingerBands(bot)
        self.position_info = {
            'LONG': {
                'side': 'LONG',
                'qty': 0,
                'entryPrice': 0,
                'realisedPnl': 0,
            }, 'SHORT': {
                'side': 'SHORT',
                'qty': 0,
                'entryPrice': 0,
                'realisedPnl': 0,
            }
        }  # dict
        self.current_price = None  # str

        self.percent = Decimal(0.1)
        self.income_percent = Decimal(0.06)
        self.order_count = 3
        self.order_data_list = {'LONG': {}, 'SHORT': {}}
        self.reduce_order_list = {'LONG': [], 'SHORT': []}
        self.reduce_order_id_list = {'LONG': [], 'SHORT': []}
        self.count_reduce_order_filled = {'LONG': 0, 'SHORT': 0}

        self.psn_locker = threading.Lock()

    def preparatory_actions(self):
        try:
            change_position_mode(self.bot)
        except:
            pass
        try:
            set_leverage(self.bot)
        except:
            pass

    def check_opened_psn(self):
        psn_data = get_position_inform(self.bot)
        if float(psn_data[0]['qty']) != 0 and float(psn_data[1]['qty']) != 0:
            self.position_info['LONG'] = psn_data[0] if psn_data[0]['side'] == 'LONG' else psn_data[1]
            self.position_info['SHORT'] = psn_data[0] if psn_data[0]['side'] == 'SHORT' else psn_data[1]
            self.position_info['SHORT']['entryPrice'] = abs(Decimal(self.position_info['SHORT']['entryPrice']))
            self.position_info['LONG']['entryPrice'] = Decimal(self.position_info['LONG']['entryPrice'])
            self.place_reduction_orders(psn_side='LONG')
            self.place_reduction_orders(psn_side='SHORT')
            return True
        elif float(psn_data[0]['qty']) != 0 or float(psn_data[1]['qty']) != 0:
            raise Exception(f'Одна из позиций не равна 0')
        else:
            return False

    def open_psns_with_start(self):
        while not self.current_price:
            time.sleep(0.1)

        long_order = {
            'symbol': self.symbol_name,
            'side': 'BUY',
            'positionSide': 'LONG',
            'type': 'MARKET',
            'price': self.current_price,
        }
        short_order = {
            'symbol': self.symbol_name,
            'side': 'SELL',
            'positionSide': 'SHORT',
            'type': 'MARKET',
            'price': self.current_price,
        }
        response = place_batch_order(self.bot, order_list=[long_order, short_order])

    def place_reduction_orders(self, psn_side):
        psn = self.position_info[psn_side]
        if psn['qty']:
            psn_qty = psn['qty']
            psn_price = psn['entryPrice']

            for order_number in range(self.order_count):
                order_data_class = self.calc_reduction_order(side=psn_side, qty=psn_qty, price=psn_price,
                                                             order_number=order_number)
                self.format_reduction_order(side=psn_side, order_number=order_number)

                psn_price = order_data_class.order_price
                psn_qty = order_data_class.qty_after_sold

            response = place_batch_order(self.bot, order_list=self.reduce_order_list[psn_side])
            self.reduce_order_id_list[psn_side] = [order['orderId'] for order in response]

    def place_next_reduction_order(self, side):
        last_order_index = max(self.order_data_list[side])
        last_order = self.order_data_list[side][last_order_index]

        self.calc_reduction_order(side, last_order.order_price, last_order.qty_after_sold, last_order_index)
        order = self.format_reduction_order(side, last_order_index)

        response = place_order(self.bot, side=side, position_side=order['positionSide'], order_type='LIMIT',
                               price=order['price'], qty=order['qty'])
        self.reduce_order_id_list[side].append(response['orderId'])

    def calc_reduction_order(self, side, price, qty, order_number):
        if side == 'LONG':
            order_data_class = LongReduceOrder(qty=qty, price=price, percent=self.percent)
        elif side == 'SHORT':
            order_data_class = ShortReduceOrder(qty=qty, price=price, percent=self.percent)

        self.order_data_list[side][order_number] = order_data_class
        return order_data_class

    def format_reduction_order(self, side, order_number):
        order_data_class = self.order_data_list[side][order_number]
        order = {
            'symbol': self.symbol_name,
            'side': 'BUY' if side == 'SHORT' else 'SELL',
            'positionSide': side,
            'type': 'LIMIT',
            'price': str(order_data_class.price),
            'qty': str(order_data_class.coin_sold_count.quantize(Decimal(self.symbol.qtyStep), rounding=ROUND_UP)),
        }
        self.reduce_order_list[side].append(order)
        return order

    def calc_end_cycle_price(self):
        left = Decimal(self.symbol.minPrice)
        right = Decimal(self.symbol.maxPrice)
        side = 'LONG' if self.position_info['LONG']['qty'] > self.position_info['SHORT']['qty'] else 'SHORT'

        def calc_pnl_for_price(price):
            pnl = 0
            for side in ['LONG', 'SHORT']:
                pnl += self.position_info[side]['realisedPnl']
                pnl += self.position_info[side]['qty'] * price - self.bot.qty * self.bot.isLeverage
            return pnl

        expected_pnl = (self.bot.qty * 2) * self.income_percent  # Заменить income_percent
        while left <= right:
            mid = round(left + (right - left) / 2, self.symbol.priceScale)
            pnl = calc_pnl_for_price(mid)

            if pnl == expected_pnl:
                return mid
            elif pnl < expected_pnl and side == 'LONG' or pnl > expected_pnl and side == 'SHORT':
                left = mid + self.symbol.tickSize
            elif pnl > expected_pnl and side == 'LONG' or pnl < expected_pnl and side == 'SHORT':
                right = mid - self.symbol.tickSize
        return None

    # def place_reduction_orders(self, psn_side):
    #     psn = self.position_info[psn_side]
    #     if psn['qty']:
    #         psn_qty = Decimal(psn['qty'])
    #         psn_price = Decimal(psn['entryPrice'])
    #         psn_cost = psn_price * psn_qty
    #
    #         if psn_side == 'LONG':
    #             for number_order in range(self.order_count):
    #                 order_price = psn_price * (1 + self.percent)
    #                 order_cost = order_price * psn_qty
    #                 cost_diff = abs(order_cost - psn_cost)
    #                 coin_sold_count = cost_diff / order_price
    #                 qty_after_sold = psn_qty - coin_sold_count
    #
    #                 order_data = {
    #                     'order_price': round(order_price, 10),
    #                     'order_cost': round(order_cost, 10),
    #                     'cost_diff': round(cost_diff, 10),
    #                     'qty_after_sold': round(qty_after_sold, 10),
    #                     'coin_sold_count': round(coin_sold_count, 10),
    #                 }
    #                 self.order_data_list['LONG'][number_order] = order_data
    #
    #                 coin_sold_count = round(coin_sold_count, 3)
    #                 order = {
    #                     'symbol': self.symbol_name,
    #                     'side': 'SELL',
    #                     'positionSide': 'LONG',
    #                     'type': 'LIMIT',
    #                     'price': str(order_price),
    #                     'qty': str(coin_sold_count),
    #                 }
    #                 self.reduce_order_list['LONG'].append(order)
    #
    #                 psn_qty = qty_after_sold
    #                 psn_price = order_price
    #                 psn_cost = psn_price * psn_qty
    #
    #             response = place_batch_order(self.bot, order_list=self.reduce_order_list['LONG'])
    #             self.reduce_order_id_list['LONG'] = [order['orderId'] for order in response]
    #
    #         elif psn_side == 'SHORT':
    #             for number_order in range(self.order_count):
    #                 order_price = psn_price / (1 + self.percent)
    #                 order_cost = order_price * psn_qty
    #                 cost_after_reduction = order_cost / (1 + self.percent)
    #                 qty_after_sold = cost_after_reduction / order_price
    #                 coin_sold_count = psn_qty - qty_after_sold
    #
    #                 order_data = {
    #                     'order_price': round(order_price, 10),
    #                     'order_cost': round(order_cost, 10),
    #                     'cost_after_reduction': round(cost_after_reduction, 10),
    #                     'qty_after_sold': round(qty_after_sold, 10),
    #                     'coin_sold_count': round(coin_sold_count, 10),
    #                 }
    #                 self.order_data_list['SHORT'][number_order] = order_data
    #
    #                 coin_sold_count = round(coin_sold_count, 3)
    #                 order = {
    #                     'symbol': self.symbol_name,
    #                     'side': 'BUY',
    #                     'positionSide': 'SHORT',
    #                     'type': 'LIMIT',
    #                     'price': str(order_price),
    #                     'qty': str(coin_sold_count),
    #                 }
    #                 self.reduce_order_list['SHORT'].append(order)
    #
    #                 psn_qty = qty_after_sold
    #                 psn_price = order_price
    #
    #             response = place_batch_order(self.bot, order_list=self.reduce_order_list['SHORT'])
    #             self.reduce_order_id_list['SHORT'] = [order['orderId'] for order in response]
    #
    #     for orders in self.order_data_list.values():
    #         print()
    #         for order in orders.values():
    #             print(order)
    #         print()
