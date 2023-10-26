import time
from decimal import Decimal

from api_v5 import get_list, cancel_all, switch_position_mode, set_leverage, get_current_price, set_trading_stop, \
    get_open_orders, cancel_order, amend_order
from bots.bot_logic import get_quantity_from_price
from orders.models import Order


class StepHedgeClassLogic:
    def __init__(self, bot, step_hg):
        self.bot = bot
        self.step_hg = step_hg
        self.bot_id = bot.pk
        self.account = bot.account
        self.category = bot.category
        self.symbol = bot.symbol
        self.leverage = bot.isLeverage
        self.price = bot.price
        self.round_number = int(bot.symbol.priceScale)
        self.symbol_list = get_list(bot.account, symbol=bot.symbol)
        self.order_book = None
        self.short1invest = Decimal(step_hg.short1invest)
        self.long1invest = Decimal(step_hg.long1invest)
        self.tp_pnl_percent = Decimal(step_hg.tp_pnl_percent)
        self.pnl_short_avg = Decimal(step_hg.pnl_short_avg)
        self.pnl_long_avg = Decimal(step_hg.pnl_long_avg)
        self.margin_short_avg = Decimal(step_hg.margin_short_avg)
        self.margin_long_avg = Decimal(step_hg.margin_long_avg)
        self.tp_price_dict = dict()
        self.new_psn_price_dict = dict()
        self.new_psn_orderId_dict = dict()
        self.tickSize = Decimal(self.bot.symbol.tickSize)

    def preparatory_actions(self):
        # append_thread_or_check_duplicate(self.bot_id)
        cancel_all(self.account, self.category, self.symbol)
        switch_position_mode(self.bot)
        set_leverage(self.account, self.category, self.symbol, self.leverage, self.bot)

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

    def checking_opened_positions(self):
        if float(self.symbol_list[0]['size']) != 0 and float(self.symbol_list[1]['size']) != 0:
            return True

    def checking_opened_position(self, position_number):
        if Decimal(self.symbol_list[position_number]['size']) != 0:
            return True

    def checking_opened_new_psn_order(self, position_number):
        if self.order_book and len(self.order_book) > 0:
            position_idx = position_number + 1
            for order in self.order_book:
                if position_idx == order['positionIdx']:
                    if order['orderStatus'] == 'Untriggered' and order['reduceOnly'] is False:
                        self.new_psn_orderId_dict[position_number] = order['orderId']
                        return True

    def buy_by_market(self):
        current_price = get_current_price(self.account, self.category, self.symbol)
        for order_side in ['Buy', 'Sell']:
            if order_side == 'Buy':
                qty = get_quantity_from_price(self.long1invest, current_price, self.symbol.minOrderQty, self.leverage)
            else:
                qty = get_quantity_from_price(self.short1invest, current_price, self.symbol.minOrderQty, self.leverage)
            order = Order.objects.create(
                bot=self.bot,
                category=self.category,
                symbol=self.symbol.name,
                side=order_side,
                orderType="Market",
                qty=qty,
            )

    def buy_by_limit(self):
        current_price = get_current_price(self.account, self.category, self.symbol)
        trigger_direction = 1 if self.price > current_price else 2
        for order_side in ['Buy', 'Sell']:
            if order_side == 'Buy':
                qty = get_quantity_from_price(self.long1invest, self.price, self.symbol.minOrderQty, self.leverage)
            else:
                qty = get_quantity_from_price(self.short1invest, self.price, self.symbol.minOrderQty, self.leverage)
            order = Order.objects.create(
                bot=self.bot,
                category=self.category,
                symbol=self.symbol.name,
                side=order_side,
                orderType="Market",
                qty=qty,
                price=str(self.price),
                triggerDirection=trigger_direction,
                triggerPrice=str(self.price),
            )

    def place_tp_order(self, position_number):
        position_idx = position_number + 1
        tp_qty = Decimal(self.symbol_list[position_number]['size'])

        if position_number == 0:
            # tp_margin = self.long1invest * (1 + self.tp_pnl_percent / 100)
            # self.tp_price_dict[position_number] = round(tp_margin * self.leverage / tp_qty, self.round_number)
            self.tp_price_dict[position_number] = round(Decimal(self.symbol_list[position_number]['avgPrice']) * Decimal(1 + self.tp_pnl_percent / 100 / self.leverage), self.round_number)
        else:
            # tp_margin = self.short1invest * (1 - self.tp_pnl_percent / 100)
            # self.tp_price_dict[position_number] = round(tp_margin * self.leverage / tp_qty, self.round_number)
            self.tp_price_dict[position_number] = round(Decimal(self.symbol_list[position_number]['avgPrice']) * Decimal(1 - self.tp_pnl_percent / 100 / self.leverage), self.round_number)

        return set_trading_stop(self.bot, position_idx, takeProfit=str(self.tp_price_dict[position_number]))

    def losses_check(self, position_number):
        pass

    def place_new_psn_order(self, position_number):
        current_price = get_current_price(self.account, self.category, self.symbol)
        if position_number == 0:
            price = self.tp_price_dict[position_number] + 30 * self.tickSize
            qty = get_quantity_from_price(self.long1invest, price, self.symbol.minOrderQty, self.leverage)
        else:
            price = self.tp_price_dict[position_number] - 30 * self.tickSize
            qty = get_quantity_from_price(self.short1invest, price, self.symbol.minOrderQty, self.leverage)

        trigger_direction = 1 if price > current_price else 2
        order_side = 'Buy' if position_number == 0 else 'Sell'
        self.new_psn_price_dict[position_number] = price
        order = Order.objects.create(
            bot=self.bot,
            category=self.category,
            symbol=self.symbol.name,
            side=order_side,
            orderType="Market",
            qty=qty,
            price=str(price),
            triggerDirection=trigger_direction,
            triggerPrice=str(price),
        )

    def distance_between_price_and_order_check(self, position_number):
        current_price = get_current_price(self.account, self.category, self.symbol)
        distance_between = abs(current_price - self.new_psn_price_dict[position_number]) / self.tickSize
        if distance_between > 30:
            return True

    def amend_new_psn_order(self, position_number):
        if position_number == 0:
            self.new_psn_price_dict[position_number] = self.new_psn_price_dict[position_number] - 10 * self.tickSize
        else:
            self.new_psn_price_dict[position_number] = self.new_psn_price_dict[position_number] + 10 * self.tickSize
        params = {'price': str(self.new_psn_price_dict[position_number])}
        amend_order(self.bot, self.new_psn_orderId_dict[position_number], params)
