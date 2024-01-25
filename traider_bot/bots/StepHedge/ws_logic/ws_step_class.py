import threading
import time
from decimal import Decimal

from api.api_v5_bybit import get_list, cancel_all, switch_position_mode, set_leverage, get_current_price, set_trading_stop, \
    get_open_orders, cancel_order, amend_order
from bots.bot_logic import get_quantity_from_price, logging
from bots.models import JsonObjectClass
from orders.models import Order
from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message


class WSStepHedgeClassLogic:
    def __init__(self, bot, step_hg, class_data_obj):
        self.bot = bot
        self.step_hg = step_hg
        self.class_data_obj = class_data_obj
        self.telegram_account = TelegramAccount.objects.filter(owner=bot.owner).first()
        self.bot_id = bot.pk
        self.account = bot.account
        self.category = bot.category
        self.symbol = bot.symbol
        self.leverage = bot.isLeverage
        self.price = bot.price
        self.round_number = int(bot.symbol.priceScale)
        self.symbol_list = None
        self.ws_symbol_list = dict()
        self.order_book = None
        self.short1invest = Decimal(step_hg.short1invest)
        self.long1invest = Decimal(step_hg.long1invest)
        self.tp_pnl_percent_short = Decimal(step_hg.tp_pnl_percent)
        self.tp_pnl_percent_long = Decimal(step_hg.tp_pnl_percent_long)
        self.pnl_short_avg = Decimal(step_hg.pnl_short_avg)
        self.pnl_long_avg = Decimal(step_hg.pnl_long_avg)
        self.margin_short_avg = Decimal(step_hg.margin_short_avg)
        self.margin_long_avg = Decimal(step_hg.margin_long_avg)
        self.last_price = 0
        self.tp_price_dict = dict()
        self.new_psn_price_dict = dict()
        self.psn_price_dict = dict()
        self.new_psn_orderId_dict = dict()
        self.tickSize = Decimal(self.bot.symbol.tickSize)
        self.qty_steps = self.step_hg.qty_steps
        self.qty_steps_diff = self.step_hg.qty_steps_diff
        self.entry_qty = dict()
        self.avg_trigger_price = dict()
        self.avg_order_id = dict()
        self.is_avg_psn_flag_dict = {1: False, 2: False}
        self.tp_order_executed = {1: False, 2: False}
        self.new_order_is_filled = {1: False, 2: False}

        self.locker_1 = threading.Lock()
        self.locker_2 = threading.Lock()
        self.locker_3 = threading.Lock()

    def send_telegram_notice(self, message):
        if self.telegram_account:
            chat_id = self.telegram_account.chat_id
            send_telegram_message(chat_id, bot=self.bot, message=message)

    def preparatory_actions(self):
        # append_thread_or_check_duplicate(self.bot_id)
        # cancel_all(self.account, self.category, self.symbol)
        switch_position_mode(self.bot)
        set_leverage(self.account, self.category, self.symbol, self.leverage, self.bot)
        self.update_symbol_list()

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
        if float(self.symbol_list[0]['size']) != 0 or float(self.symbol_list[1]['size']) != 0:
            return True

    def checking_2opened_positions(self):
        if float(self.symbol_list[0]['size']) != 0 and float(self.symbol_list[1]['size']) != 0:
            return True

    def checking_opened_position(self, position_number):
        if Decimal(self.symbol_list[position_number]['size']) != 0:
            return True

    def buy_by_market(self):
        cancel_all(self.account, self.category, self.symbol)
        current_price = get_current_price(self.account, self.category, self.symbol) + 3 * self.tickSize
        for order_side in ['Buy', 'Sell']:
            if order_side == 'Buy':
                qty = get_quantity_from_price(Decimal(self.step_hg.long1invest), current_price, self.symbol.minOrderQty, self.leverage)
            else:
                qty = get_quantity_from_price(Decimal(self.step_hg.short1invest), current_price, self.symbol.minOrderQty, self.leverage)
            self.entry_qty[1 if order_side == 'Buy' else 2] = qty

            if qty:
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
                qty = get_quantity_from_price(Decimal(self.step_hg.long1invest), self.price, self.symbol.minOrderQty, self.leverage)
            else:
                qty = get_quantity_from_price(Decimal(self.step_hg.short1invest), self.price, self.symbol.minOrderQty, self.leverage)
            logging(self.bot, f'buy_by_limit, trigger_direction = {trigger_direction}')
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

    # def buy_by_market_limit_order(self):
    #     current_price = get_current_price(self.account, self.category, self.symbol)
    #     for order_side in ['Buy', 'Sell']:
    #         if order_side == 'Buy':
    #             qty = get_quantity_from_price(Decimal(self.step_hg.long1invest), current_price, self.symbol.minOrderQty, self.leverage)
    #         else:
    #             qty = get_quantity_from_price(Decimal(self.step_hg.short1invest), current_price, self.symbol.minOrderQty, self.leverage)
    #
    #         order = Order.objects.create(
    #             bot=self.bot,
    #             category=self.category,
    #             symbol=self.symbol.name,
    #             side=order_side,
    #             orderType="Limit",
    #             qty=qty,
    #             price=str(current_price),
    #         )

    def place_tp_order(self, position_number):
        position_idx = self.symbol_list[position_number]['positionIdx']
        tp_size = self.symbol_list[position_number]['size']

        if self.checking_opened_position(position_number):
            psn_avg_price = Decimal(self.symbol_list[position_number]['avgPrice'])
        else:
            psn_avg_price = Decimal(self.symbol_list[0 if position_number == 1 else 1]['avgPrice'])

        if position_idx == 1:
            self.tp_price_dict[position_idx] = round(psn_avg_price * Decimal(1 + Decimal(self.step_hg.tp_pnl_percent_long) / 100 / self.leverage), self.round_number)
        else:
            self.tp_price_dict[position_idx] = round(psn_avg_price * Decimal(1 - Decimal(self.step_hg.tp_pnl_percent) / 100 / self.leverage), self.round_number)

        if self.step_hg.add_tp:
            return set_trading_stop(
                self.bot, position_idx, takeProfit=str(self.tp_price_dict[position_idx]), tpSize=tp_size)
        else:
            return set_trading_stop(
                self.bot, position_idx, takeProfit=str(self.tp_price_dict[position_idx]))

    def calculate_avg_trigger_price(self, position_idx):
        psn_entry_price = Decimal(self.ws_symbol_list[position_idx]['entryPrice'])
        if psn_entry_price > 0:
            if position_idx == 1:
                self.avg_trigger_price[position_idx] = round(
                    psn_entry_price * Decimal(str(1 - Decimal(self.step_hg.pnl_long_avg) / 100 / self.leverage)), self.round_number)
            else:
                self.avg_trigger_price[position_idx] = round(
                    psn_entry_price * Decimal(1 + Decimal(self.step_hg.pnl_short_avg) / 100 / self.leverage), self.round_number)

        # self.class_data_obj.data['avg_trigger_price'][position_idx] = str(self.avg_trigger_price[position_idx])
        # self.class_data_obj.save()

    def losses_pnl_check(self, position_number):
        position_idx = self.symbol_list[position_number]['positionIdx']
        try:
            pnl = Decimal(self.symbol_list[position_number]['unrealisedPnl'])
        except:
            pnl = 1

        if pnl < 0:
            symbol_list = self.symbol_list[position_number]
            psn_margin = Decimal(symbol_list['avgPrice']) * Decimal(symbol_list['size']) / self.leverage
            if position_idx == 1:
                if abs(pnl) > psn_margin / 100 * Decimal(self.step_hg.pnl_long_avg):
                    return True
            else:
                if abs(pnl) > psn_margin / 100 * Decimal(self.step_hg.pnl_short_avg):
                    return True

    def limit_average_psn(self, position_number):
        position_idx = self.symbol_list[position_number]['positionIdx']
        qty = Decimal(self.symbol_list[position_number]['size'])
        side = 'Buy' if position_idx == 1 else 'Sell'
        if side == 'Buy':
            avg_qty = qty * Decimal(self.step_hg.margin_long_avg) / 100
        else:
            avg_qty = qty * Decimal(self.step_hg.margin_short_avg) / 100
        order = Order.objects.create(
            bot=self.bot,
            category=self.category,
            symbol=self.symbol.name,
            side=side,
            price=str(self.avg_trigger_price[position_idx]),
            orderType="Limit",
            qty=avg_qty,
        )

    def ws_limit_average_psn(self, position_idx):
        qty = Decimal(self.ws_symbol_list[position_idx]['size'])
        if qty > 0:
            side = 'Buy' if position_idx == 1 else 'Sell'
            if side == 'Buy':
                avg_qty = qty * Decimal(self.step_hg.margin_long_avg) / 100
            else:
                avg_qty = qty * Decimal(self.step_hg.margin_short_avg) / 100
            order = Order.objects.create(
                bot=self.bot,
                category=self.category,
                symbol=self.symbol.name,
                side=side,
                price=str(self.avg_trigger_price[position_idx]),
                orderType="Limit",
                qty=avg_qty,
            )

    def average_psn(self, position_number):
        position_idx = self.symbol_list[position_number]['positionIdx']
        qty = Decimal(self.symbol_list[position_number]['size'])
        side = 'Buy' if position_idx == 1 else 'Sell'
        # current_price = get_current_price(self.account, self.category, self.symbol)
        if side == 'Buy':
            # qty = get_quantity_from_price(Decimal(self.step_hg.long1invest), current_price, self.symbol.minOrderQty, self.leverage)
            avg_qty = qty * Decimal(self.step_hg.margin_long_avg) / 100
        else:
            # qty = get_quantity_from_price(Decimal(self.step_hg.short1invest), current_price, self.symbol.minOrderQty, self.leverage)
            avg_qty = qty * Decimal(self.step_hg.margin_short_avg) / 100

        order = Order.objects.create(
            bot=self.bot,
            category=self.category,
            symbol=self.symbol.name,
            side=side,
            orderType="Market",
            qty=avg_qty,
        )
        # cancel_all(self.account, self.category, self.symbol)

    def checking_opened_new_psn_order(self, position_number):
        if self.order_book and len(self.order_book) > 0:
            position_idx = self.symbol_list[position_number]['positionIdx']
            for order in self.order_book:
                if position_idx == order['positionIdx']:
                    # if order['orderStatus'] == 'New' or order['orderStatus'] == 'PartiallyFilled':
                    #     self.new_psn_orderId_dict[position_idx] = order['orderId']
                    #     self.new_psn_price_dict[position_idx] = Decimal(order['price'])
                    #     return True
                    if order['orderStatus'] == 'Untriggered' and order['reduceOnly'] is False:
                        self.new_psn_orderId_dict[position_idx] = order['orderId']
                        self.new_psn_price_dict[position_idx] = Decimal(order['triggerPrice'])
                        return True

    def place_new_psn_order(self, position_number):
        position_idx = self.symbol_list[position_number]['positionIdx']
        current_price = get_current_price(self.account, self.category, self.symbol)
        if position_idx == 1:
            price = self.tp_price_dict[position_idx] + self.qty_steps * self.tickSize
            qty = get_quantity_from_price(Decimal(self.step_hg.long1invest), price, self.symbol.minOrderQty, self.leverage)
        else:
            price = self.tp_price_dict[position_idx] - self.qty_steps * self.tickSize
            qty = get_quantity_from_price(Decimal(self.step_hg.short1invest), price, self.symbol.minOrderQty, self.leverage)

        trigger_direction = 1 if price > current_price else 2
        order_side = 'Buy' if position_idx == 1 else 'Sell'
        self.new_psn_price_dict[position_idx] = price
        logging(self.bot, f'place_new_psn_order, trigger_direction = {trigger_direction}')
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
        position_idx = self.symbol_list[position_number]['positionIdx']
        current_price = get_current_price(self.account, self.category, self.symbol)
        distance_between = abs(current_price - self.new_psn_price_dict[position_idx]) / self.tickSize
        if distance_between > self.qty_steps:
            return True

    def amend_new_psn_order(self, position_number):
        position_idx = self.symbol_list[position_number]['positionIdx']
        if position_idx == 1:
            self.new_psn_price_dict[position_idx] -= self.qty_steps_diff * self.tickSize
        else:
            self.new_psn_price_dict[position_idx] += self.qty_steps_diff * self.tickSize
        params = {'triggerPrice': str(self.new_psn_price_dict[position_idx])}
        amend_order(self.bot, self.new_psn_orderId_dict[position_idx], params)

    def psn_size_bigger_then_start(self, position_number):
        position_idx = self.symbol_list[position_number]['positionIdx']
        qty = Decimal(self.symbol_list[position_number]['size'])
        price = Decimal(self.symbol_list[position_number]['avgPrice'])
        first_invest = Decimal(self.step_hg.long1invest) if position_idx == 1 else Decimal(self.step_hg.short1invest)
        # Это делается затем чтобы first_invest точно был больше начального значения, но меньше усредненного
        first_invest = first_invest * (1 + (Decimal(self.step_hg.margin_long_avg) / 100) / 2)
        if qty * price / self.leverage > first_invest:
            return True

    def tp_full_size_psn_check(self, position_number):
        position_idx = self.symbol_list[position_number]['positionIdx']
        full_qty = Decimal(self.symbol_list[position_number]['size'])
        fill_qty = 0
        for order in self.order_book:
            if order['positionIdx'] == position_idx and order['reduceOnly'] is True:
                fill_qty += Decimal(order['leavesQty'])
        if full_qty <= fill_qty:
            return True

    def add_tp(self, position_number):
        position_idx = self.symbol_list[position_number]['positionIdx']
        psn_price = Decimal(self.symbol_list[position_number]['avgPrice'])
        excess_qty = Decimal(self.symbol_list[position_number]['size'])
        if position_idx == 1:
            tp_price = round(psn_price * Decimal(1 + Decimal(self.step_hg.tp_pnl_percent_long) / 100 / self.leverage), self.round_number)
        else:
            tp_price = round(psn_price * Decimal(1 - Decimal(self.step_hg.tp_pnl_percent) / 100 / self.leverage), self.round_number)

        for order in self.order_book:
            if order['positionIdx'] == position_idx and order['reduceOnly'] is True:
                excess_qty -= Decimal(order['leavesQty'])
        set_trading_stop(self.bot, position_idx, takeProfit=str(tp_price), tpSize=str(excess_qty))

    def place_nipple_on_tp(self, position_number):
        position_idx = self.symbol_list[position_number]['positionIdx']
        if self.tp_price_dict[position_idx]:
            current_price = get_current_price(self.account, self.category, self.symbol)
            if position_idx == 1:
                price = self.tp_price_dict[position_idx]
                qty = get_quantity_from_price(Decimal(self.step_hg.long1invest), price, self.symbol.minOrderQty, self.leverage)
            else:
                price = self.tp_price_dict[position_idx]
                qty = get_quantity_from_price(Decimal(self.step_hg.short1invest), price, self.symbol.minOrderQty, self.leverage)

            trigger_direction = 1 if price > current_price else 2
            order_side = 'Buy' if position_idx == 1 else 'Sell'
            self.new_psn_price_dict[position_idx] = price
            logging(self.bot, f'place_nipple_on_tp, trigger_direction = {trigger_direction}')
            Order.objects.create(
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

    def ws_place_tp_order(self, order, status='Filled'):
        position_idx = order['positionIdx']
        tp_size = Decimal(order['qty'])

        if status == 'Filled':
            psn_avg_price = Decimal(order['avgPrice'])

            if position_idx == 1:
                self.tp_price_dict[position_idx] = round(
                    psn_avg_price * Decimal(1 + Decimal(self.step_hg.tp_pnl_percent_long) / 100 / self.leverage),
                    self.round_number)
            else:
                self.tp_price_dict[position_idx] = round(
                    psn_avg_price * Decimal(1 - Decimal(self.step_hg.tp_pnl_percent) / 100 / self.leverage),
                    self.round_number)

        elif status == 'Deactivated':
            self.tp_price_dict[position_idx] = Decimal(order['triggerPrice'])

        if self.step_hg.add_tp:
            # print('ADD_TP RESPONSE -------- ')
            return set_trading_stop(
                self.bot, position_idx, takeProfit=str(self.tp_price_dict[position_idx]), tpSize=tp_size)
        else:
            response = set_trading_stop(self.bot, position_idx, takeProfit=str(self.tp_price_dict[position_idx]))
            # print('TP RESPONSE: ', response)
            # print()
            return response

    def ws_place_new_psn_order(self, order, status='Filled'):
        position_idx = order['positionIdx']
        if status == 'Filled':
            current_price = Decimal(order['avgPrice'])

            if position_idx == 1:
                if self.step_hg.is_nipple_active:
                    price = self.tp_price_dict[position_idx] + self.qty_steps * self.tickSize
                else:
                    price = self.tp_price_dict[position_idx]
                qty = get_quantity_from_price(Decimal(self.step_hg.long1invest), price, self.symbol.minOrderQty, self.leverage)
            else:
                if self.step_hg.is_nipple_active:
                    price = self.tp_price_dict[position_idx] - self.qty_steps * self.tickSize
                else:
                    price = self.tp_price_dict[position_idx]
                qty = get_quantity_from_price(Decimal(self.step_hg.short1invest), price, self.symbol.minOrderQty, self.leverage)

            trigger_direction = 1 if price > current_price else 2
            order_side = 'Buy' if position_idx == 1 else 'Sell'
            self.new_psn_price_dict[position_idx] = price
            logging(self.bot, f'ws_place_new_psn_order, trigger_direction = {trigger_direction}')
            Order.objects.create(
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
        elif status == 'Deactivated':
            price = Decimal(order['triggerPrice'])
            self.new_psn_price_dict[position_idx] = price
            Order.objects.create(
                bot=self.bot,
                category=self.category,
                symbol=self.symbol.name,
                side=order['side'],
                orderType="Market",
                qty=order['qty'],
                price=order['triggerPrice'],
                triggerDirection=order['triggerDirection'],
                triggerPrice=order['triggerPrice'],
            )
        # print('PLACE ORDER AFTER -', order['orderId'])
        # print()

    def ws_replace_new_psn_order(self, position_idx):
        current_price = get_current_price(self.account, self.category, self.symbol)
        price = self.new_psn_price_dict[position_idx]
        if position_idx == 1:
            qty = get_quantity_from_price(Decimal(self.step_hg.long1invest), price, self.symbol.minOrderQty, self.leverage)
        else:
            qty = get_quantity_from_price(Decimal(self.step_hg.short1invest), price, self.symbol.minOrderQty, self.leverage)

        trigger_direction = 1 if price > current_price else 2
        order_side = 'Buy' if position_idx == 1 else 'Sell'
        logging(self.bot, f'ws_replace_new_psn_order, trigger_direction = {trigger_direction}')
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

    def ws_average_psn_by_market(self, position_idx):
        qty = Decimal(self.ws_symbol_list[position_idx]['size'])
        side = 'Buy' if position_idx == 1 else 'Sell'
        if side == 'Buy':
            avg_qty = qty * Decimal(self.step_hg.margin_long_avg) / 100
        else:
            avg_qty = qty * Decimal(self.step_hg.margin_short_avg) / 100

        if self.bot.max_margin:
            current_margin = self.get_current_margin()
            avg_margin = avg_qty * Decimal(self.ws_symbol_list[position_idx]['entryPrice']) / self.leverage
            total_margin = current_margin + avg_margin

            if total_margin < self.bot.max_margin:
                order = Order.objects.create(
                    bot=self.bot,
                    category=self.category,
                    symbol=self.symbol.name,
                    side=side,
                    orderType="Market",
                    qty=avg_qty,
                )

                message = f'Позиция {side} была усреднена на {avg_qty} {self.symbol.name}'
                self.send_telegram_notice(message)

            else:
                logging(self.bot,
                        f'Margin limit reached. Current limit {self.bot.max_margin}. Margin after avg {total_margin}')
        else:
            order = Order.objects.create(
                bot=self.bot,
                category=self.category,
                symbol=self.symbol.name,
                side=side,
                orderType="Market",
                qty=avg_qty,
            )

            message = f'Позиция {side} была усреднена на {avg_qty} {self.symbol.name}'
            self.send_telegram_notice(message)

    def ws_amend_tp_order(self, position_idx):
        new_psn_price = Decimal(self.ws_symbol_list[position_idx]['entryPrice'])
        if position_idx == 1:
            self.tp_price_dict[position_idx] = round(new_psn_price * Decimal(1 + Decimal(self.step_hg.tp_pnl_percent_long) / 100 / self.leverage), self.round_number)
        elif position_idx == 2:
            self.tp_price_dict[position_idx] = round(new_psn_price * Decimal(1 - Decimal(self.step_hg.tp_pnl_percent) / 100 / self.leverage), self.round_number)

        set_trading_stop(self.bot, position_idx, takeProfit=str(self.tp_price_dict[position_idx]))

    def ws_amend_new_psn_order(self, position_idx, current_price=False):
        if current_price:
            current_price = get_current_price(self.account, self.category, self.symbol)
            if position_idx == 1:
                trigger_price = current_price + self.tickSize
            else:
                trigger_price = current_price - self.tickSize
        else:
            if self.step_hg.is_nipple_active:
                if position_idx == 1:
                    trigger_price = self.tp_price_dict[position_idx] + self.qty_steps * self.tickSize
                else:
                    trigger_price = self.tp_price_dict[position_idx] - self.qty_steps * self.tickSize
            else:
                trigger_price = self.tp_price_dict[position_idx]

        params = {'triggerPrice': str(trigger_price)}
        amend_order(self.bot, self.new_psn_orderId_dict[position_idx], params)

    def ws_amend_avg_psn_order(self, position_idx):
        params = {'price': str(self.avg_trigger_price[position_idx])}
        # print("РЕДАКТИРОВАНИЕ УСРЕДНЯЮЩЕГО ОРДЕРА", amend_order(self.bot, self.avg_order_id[position_idx], data=params))

    def ws_checking_opened_new_psn_order(self, position_idx):
        if self.order_book and len(self.order_book) > 0:
            for order in self.order_book:
                if position_idx == order['positionIdx']:
                    if order['orderStatus'] == 'Untriggered' and order['reduceOnly'] is False:
                        self.new_psn_orderId_dict[position_idx] = order['orderId']
                        self.new_psn_price_dict[position_idx] = Decimal(order['triggerPrice'])
                        return True

    def order_missed_check(self, position_idx):
        current_price = get_current_price(self.account, self.category, self.symbol)

        if position_idx == 1 and current_price > self.new_psn_price_dict[position_idx]:
            return True
        elif position_idx == 2 and current_price < self.new_psn_price_dict[position_idx]:
            return True

    def not_new_order_is_filled(self, position_idx):
        with self.locker_1:
            if not self.new_order_is_filled[position_idx]:
                self.new_order_is_filled[position_idx] = True
                return True

    def get_current_margin(self):
        total_margin = 0
        for i in [1, 2]:
            margin = Decimal(self.ws_symbol_list[i]['size']) * Decimal(self.ws_symbol_list[i]['entryPrice']) / self.leverage
            total_margin += margin
        return total_margin





