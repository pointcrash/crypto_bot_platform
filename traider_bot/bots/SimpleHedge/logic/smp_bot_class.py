from decimal import Decimal

from api_v5 import get_list, cancel_all, switch_position_mode, set_leverage, get_current_price, set_trading_stop, \
    get_open_orders
from bots.bot_logic import get_quantity_from_price
from orders.models import Order
from single_bot.logic.work import append_thread_or_check_duplicate


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

    def preparatory_actions(self):
        append_thread_or_check_duplicate(self.bot_id)
        cancel_all(self.account, self.category, self.symbol)
        switch_position_mode(self.bot)
        set_leverage(self.account, self.category, self.symbol, self.leverage, self.bot)
        self.bot.bin_order = False
        self.bot.save()

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
        if len(self.order_book) > 0:
            position_idx = position_number + 1
            for order in self.order_book:
                if position_idx == order['positionIdx']:
                    return True

    def update_symbol_list(self):
        self.symbol_list = get_list(self.account, symbol=self.symbol)

    def update_order_book(self):
        self.order_book = get_open_orders(self.bot)

    def cancel_all_orders_for_smp_hg(self):
        cancel_all(self.account, self.category, self.symbol)

    def calculate_tp_size(self):
        self.tp_size = self.first_order_qty * Decimal(self.smp_hg.tpap) / 100

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

        if position_size == self.first_order_qty:
            return '='
        elif position_size > self.first_order_qty:
            return '>'
        else:
            return '<'

    def lower_position(self, position_number):
        side = 'Buy' if position_number == 0 else 'Sell'
        avg_qty = str(self.first_order_qty - Decimal(self.symbol_list[position_number]['size']))
        price = self.symbol_list[position_number]['avgPrice']

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
        position_idx_avg = position_number + 1
        entry_price = Decimal(self.symbol_list[position_number]['avgPrice'])
        tp_sl_size = abs(self.first_order_qty - Decimal(self.symbol_list[position_number]['size']))
        tp_sl_response = set_trading_stop(self.bot, position_idx_avg, takeProfit=str(entry_price), tpSize=str(tp_sl_size))
        if tp_sl_response['retMsg'] != 'OK':
            tp_sl_response = set_trading_stop(self.bot, position_idx_avg, stopLoss=str(entry_price),
                                              tpSize=str(tp_sl_size))

    def equal_position(self, position_number):
        position_idx = position_number + 1

        if position_number == 0:
            tp_price = round(Decimal(self.symbol_list[0]['avgPrice']) * (1 + Decimal(self.smp_hg.tppp) / 100),
                             self.round_number)
        else:
            tp_price = round(Decimal(self.symbol_list[1]['avgPrice']) * (1 - Decimal(self.smp_hg.tppp) / 100),
                             self.round_number)

        set_trading_stop(self.bot, position_idx, takeProfit=str(tp_price), tpSize=str(self.tp_size))































