import time
from decimal import Decimal

from api_test.api_v5_bybit import get_list, cancel_all, switch_position_mode, set_leverage, get_current_price, set_trading_stop, \
    get_open_orders, cancel_order
from bots.general_functions import get_quantity_from_price
from orders.models import Order


class SimpleHedgeClassLogic:
    def __init__(self, bot, smp_hg):
        self.bot = bot
        self.smp_hg = smp_hg
        self.bot_id = bot.pk
        self.account = bot.account
        self.category = bot.category
        self.symbol = bot.symbol
        self.leverage = bot.isLeverage
        self.price = bot.price
        self.round_number = int(bot.symbol.priceScale)
        self.avg_order_links_id = {1: f'{bot.take1}', 2: f'{bot.take2}'}
        self.symbol_list = get_list(bot.account, symbol=bot.symbol)
        self.order_book = None
        self.psn_add_flag = 0
        self.psn_add_flag_2 = False
        self.first_order_qty = None
        self.tp_size = None
        self.add_psn_flag = {0: False, 1: False}
        self.orders_equalize = {0: None, 1: None}

    def preparatory_actions(self):
        # append_thread_or_check_duplicate(self.bot_id)
        cancel_all(self.account, self.category, self.symbol)
        switch_position_mode(self.bot)
        set_leverage(self.account, self.category, self.symbol, self.leverage, self.bot)

    def calc_first_order_qty(self):
        time.sleep(1)
        self.update_symbol_list()
        self.first_order_qty = Decimal(self.symbol_list[0]['size'])

    def checking_opened_positions(self):
        if float(self.symbol_list[0]['size']) != 0 and float(self.symbol_list[1]['size']) != 0:
            self.first_order_qty = get_quantity_from_price(
                self.bot.qty,
                Decimal(self.symbol_list[0]['avgPrice']),
                self.symbol.minOrderQty,
                self.leverage
            )
            self.calculate_tp_size()
            return True

    def checking_opened_order(self, position_number):
        if self.order_book and len(self.order_book) > 0:
            position_idx = self.symbol_list[position_number]['positionIdx']

            for order in self.order_book:
                if position_idx == order['positionIdx']:
                    return True

    def checking_opened_order_for_lower_psn(self, position_number):
        if self.order_book and len(self.order_book) > 0:
            position_idx = self.symbol_list[position_number]['positionIdx']
            for order in self.order_book:
                if position_idx == order['positionIdx']:
                    status = order['orderStatus']
                    if (status == 'New' or status == 'PartiallyFilled') and order['reduceOnly'] is False:
                        return order

    def checking_change_qty_for_order_lower_psn(self, position_number, order):
        if Decimal(order['qty']) < self.first_order_qty - Decimal(self.symbol_list[position_number]['size']):
            cancel_order(self.bot, order['orderId'])
            return True

    def update_symbol_list(self):
        self.symbol_list = get_list(self.account, symbol=self.symbol)
        if self.symbol_list is None:
            count = 0
            while self.symbol_list is None or count < 60:
                time.sleep(1)
                count += 1
                self.symbol_list = get_list(self.account, symbol=self.symbol)

    def update_order_book(self):
        status_req, self.order_book = get_open_orders(self.bot)
        if status_req not in 'OK':
            count = 0
            while status_req not in 'OK' or count < 60:
                time.sleep(1)
                count += 1
                status_req, self.order_book = get_open_orders(self.bot)
        return status_req

    def cancel_all_orders(self):
        cancel_all(self.account, self.category, self.symbol)

    def cancel_order(self, order_id):
        cancel_order(self.bot, order_id)

    def cancel_equalize_orders(self):
        for num in range(2):
            if self.orders_equalize[num] is not None:
                if self.orders_equalize[num] in [order['orderId'] for order in self.order_book]:
                    self.cancel_order(self.orders_equalize[num])
                    self.orders_equalize[num] = None

    def calculate_tp_size(self):
        self.tp_size = (self.first_order_qty * Decimal(self.smp_hg.tpap) / 100).quantize(Decimal(self.symbol.minOrderQty))

    def buy_by_market(self):
        current_price = get_current_price(self.account, self.category, self.symbol)
        self.first_order_qty = get_quantity_from_price(self.bot.qty, current_price, self.symbol.minOrderQty, self.leverage)
        self.calculate_tp_size()

        for order_side in ['Buy', 'Sell']:
            order = Order.objects.create(
                bot=self.bot,
                category=self.category,
                symbol=self.symbol.name,
                side=order_side,
                orderType="Market",
                qty=self.first_order_qty,
            )

    def buy_by_limit(self):
        current_price = get_current_price(self.account, self.category, self.symbol)
        self.first_order_qty = get_quantity_from_price(self.bot.qty, self.price, self.symbol.minOrderQty, self.leverage)
        trigger_direction = 1 if self.price > current_price else 2
        self.calculate_tp_size()

        for order_side in ['Buy', 'Sell']:
            order = Order.objects.create(
                bot=self.bot,
                category=self.category,
                symbol=self.symbol.name,
                side=order_side,
                orderType="Market",
                qty=self.first_order_qty,
                price=str(self.price),
                triggerDirection=trigger_direction,
                triggerPrice=str(self.price),
            )

    def take_position_status(self, position_number):
        position_size = Decimal(self.symbol_list[position_number]['size'])

        if position_size == 0:
            return 'Error'
        elif position_size == self.first_order_qty:
            return '='
        elif position_size > self.first_order_qty:
            return '>'
        elif position_size < self.first_order_qty:
            return '<'

    def lower_position(self, position_number):
        position_idx = self.symbol_list[position_number]['positionIdx']
        side = 'Buy' if position_idx == 1 else 'Sell'
        avg_qty = str(self.first_order_qty - Decimal(self.symbol_list[position_number]['size']))
        price = self.symbol_list[position_number]['avgPrice']
        self.add_psn_flag[position_number] = True

        order = Order.objects.create(
            bot=self.bot,
            category=self.category,
            symbol=self.symbol.name,
            side=side,
            orderType="Limit",
            qty=avg_qty,
            price=price,
        )

    def higher_position(self, position_number):
        position_idx_avg = self.symbol_list[position_number]['positionIdx']
        entry_price = Decimal(self.symbol_list[position_number]['avgPrice'])

        self.first_order_qty = get_quantity_from_price(
            self.bot.qty,
            Decimal(self.symbol_list[0]['avgPrice']),
            self.symbol.minOrderQty,
            self.leverage)
        self.calculate_tp_size()

        tp_sl_size = abs(self.first_order_qty - Decimal(self.symbol_list[position_number]['size']))
        tp_sl_response = set_trading_stop(self.bot, position_idx_avg, takeProfit=str(entry_price), tpSize=str(tp_sl_size))
        if tp_sl_response['retMsg'] != 'OK':
            tp_sl_response = set_trading_stop(self.bot, position_idx_avg, stopLoss=str(entry_price),
                                              tpSize=str(tp_sl_size))

    def equal_position(self, position_number, tp_count):
        position_idx = self.symbol_list[position_number]['positionIdx']

        if position_idx == 1:
            tp_price = round(Decimal(self.symbol_list[0]['avgPrice']) * (1 + Decimal(self.smp_hg.tppp) * tp_count / 100),
                             self.round_number)
        else:
            tp_price = round(Decimal(self.symbol_list[1]['avgPrice']) * (1 - Decimal(self.smp_hg.tppp) * tp_count / 100),
                             self.round_number)

        return set_trading_stop(self.bot, position_idx, takeProfit=str(tp_price), tpSize=str(self.tp_size))

    def sale_at_better_price(self, position_number):
        current_price = get_current_price(self.account, self.category, self.symbol)
        if position_number == 0:
            tp_price = round(Decimal(self.symbol_list[0]['avgPrice']) * (1 + Decimal(self.smp_hg.tppp) / 100),
                             self.round_number)
            if current_price >= tp_price:
                Order.objects.create(
                    bot=self.bot,
                    category=self.category,
                    symbol=self.symbol.name,
                    side='Sell',
                    orderType='Market',
                    qty=self.tp_size,
                    is_take=True,
                )
        else:
            tp_price = round(Decimal(self.symbol_list[1]['avgPrice']) * (1 - Decimal(self.smp_hg.tppp) / 100),
                             self.round_number)
            if current_price <= tp_price:
                Order.objects.create(
                    bot=self.bot,
                    category=self.category,
                    symbol=self.symbol.name,
                    side='Buy',
                    orderType='Market',
                    qty=self.tp_size,
                    is_take=True,
                )

    def cancel_tp_orders(self, position_number):
        if self.order_book and len(self.order_book) > 0:
            position_idx = self.symbol_list[position_number]['positionIdx']
            for order in self.order_book:
                if position_idx == order['positionIdx']:
                    if order['orderStatus'] == 'Untriggered' and order['reduceOnly'] is True:
                        cancel_order(self.bot, order['orderId'])

    def psn_price_difference_calculation(self):
        if Decimal(self.symbol_list[0]['avgPrice']) == Decimal(self.symbol_list[1]['avgPrice']):
            return 0
        else:
            return abs(Decimal(self.symbol_list[0]['avgPrice']) - Decimal(self.symbol_list[1]['avgPrice']))

    def order_equalize_check(self):
        if len(self.order_book) == 2:
            if self.order_book[0]['orderStatus'] == 'New' or self.order_book[0]['orderStatus'] == 'PartiallyFilled':
                if self.order_book[1]['orderStatus'] == 'New' or self.order_book[1]['orderStatus'] == 'PartiallyFilled':
                    self.orders_equalize[0] = self.order_book[0]['orderId']
                    self.orders_equalize[1] = self.order_book[1]['orderId']
                    return True

    def equalize_positions_price(self, difference):
        cancel_all(self.account, self.category, self.symbol)

        for position_number in range(2):
            position_idx = self.symbol_list[position_number]['positionIdx']
            avg_price = Decimal(self.symbol_list[position_number]['avgPrice'])
            qty = Decimal(self.symbol_list[position_number]['size'])
            if position_idx == 1:
                price = avg_price - difference * 2
            else:
                price = avg_price + difference * 2
            Order.objects.create(
                bot=self.bot,
                category=self.category,
                symbol=self.symbol.name,
                side='Buy' if position_idx == 1 else 'Sell',
                orderType='Limit',
                qty=qty,
                price=price
            )



























