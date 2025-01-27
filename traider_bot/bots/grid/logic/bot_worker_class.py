import logging
import time
from decimal import Decimal, ROUND_UP

from binance.exceptions import BinanceAPIException
from django.core.cache import cache
from django.utils import timezone

from api_2.api_aggregator import change_position_mode, set_leverage, get_quantity_from_price, place_batch_order, \
    place_order, get_open_orders, get_pnl_by_time
from bots.general_functions import custom_user_bot_logging, custom_logging
from bots.models import BotModel, BotsData
from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message


class WorkGridClass:
    def __init__(self, bot):
        self.bot = bot
        self.account = bot.account
        self.tg_acc = TelegramAccount.objects.filter(owner=bot.owner).first()
        self.grid = bot.grid
        self.symbol = bot.symbol.name
        self.current_price = None
        self.price_step = self.get_price_step()
        self.bots_data = None

        self.logger = self.get_logger_for_bot_ws_msg(bot.id)
        self.last_deal_time = timezone.now()

    def cached_data(self, key, value):
        cache.set(f'bot{self.bot.id}_{key}', str(value))

    def get_logger_for_bot_ws_msg(self, bot_id):
        formatter = logging.Formatter('%(message)s')

        logger = logging.getLogger(f'BOT_{bot_id}_METRICS')
        logger.setLevel(logging.DEBUG)

        handler = logging.FileHandler(f'logs/bots/ws_data/bot_{bot_id}_metrics.log')
        handler.setFormatter(formatter)
        logger.handlers.clear()
        logger.addHandler(handler)

        return logger

    def preparatory_actions(self):
        custom_user_bot_logging(self.bot, f' Бот запущен')
        self.bots_data_init()

        try:
            change_position_mode(self.bot)
        except:
            pass
        try:
            set_leverage(self.bot)
        except:
            pass

    def get_price_step(self):
        return (self.grid.high_price - self.grid.low_price) / (self.grid.grid_count + 1)

    def initial_placing_orders(self):
        len_order_list = len(get_open_orders(self.bot))

        if len_order_list == self.grid.grid_count:
            return

        elif 0 < len_order_list < self.grid.grid_count:
            raise Exception('Incorrect number of orders')

        order_list = self.get_order_list()
        custom_logging(self.bot, f'order_list: {order_list}')
        order_chunks = [order_list[i:i + 5] for i in range(0, len(order_list), 5)]
        custom_logging(self.bot, f'order_chunks: {order_chunks}')

        responses = []
        for chunk in order_chunks:
            custom_logging(self.bot, f'chunk: {chunk}')
            response = place_batch_order(self.bot, order_list=chunk)
            custom_logging(self.bot, f'response: {response}')
            responses.append(response)

        custom_logging(self.bot, f'place batch orders responses: {responses}')
        return responses

    def get_order_list(self):
        self.current_price_waiting()

        order_list = []

        grid_number = 0
        order_price = self.grid.low_price

        while grid_number < self.grid.grid_count + 1 and self.current_price > order_price:
            order_price = self.grid.low_price + self.price_step * grid_number
            custom_logging(self.bot, f'order_price: {order_price}')

            if self.current_price - order_price >= self.price_step:
                order = self.get_open_limit_order_data(psn_side='LONG', order_price=order_price)
                order_list.append(order)

            grid_number += 1

        grid_number = 0
        order_price = self.grid.high_price

        while grid_number < self.grid.grid_count + 1 and self.current_price < order_price:
            order_price = self.grid.high_price - self.price_step * grid_number
            custom_logging(self.bot, f'order_price2: {order_price}')

            if order_price - self.current_price >= self.price_step:
                order = self.get_open_limit_order_data(psn_side='SHORT', order_price=order_price)
                order_list.append(order)

            grid_number += 1

        return order_list

    def place_new_open_order(self, psn_side, price, qty):
        side = 'BUY' if psn_side == 'LONG' else 'SELL'
        price = Decimal(price)
        price = (price - self.price_step) if psn_side == 'LONG' else (price + self.price_step)
        price = str(round(price, int(self.bot.symbol.priceScale)))

        response = place_order(bot=self.bot, side=side, order_type='LIMIT', price=price, qty=qty,
                               position_side=psn_side)

    def place_close_order(self, psn_side, price, qty):
        side = 'SELL' if psn_side == 'LONG' else 'BUY'
        price = Decimal(price)
        price = (price + self.price_step) if psn_side == 'LONG' else (price - self.price_step)
        price = str(round(price, int(self.bot.symbol.priceScale)))

        response = place_order(bot=self.bot, side=side, order_type='LIMIT', price=price, qty=qty,
                               position_side=psn_side)

    def get_open_limit_order_data(self, psn_side, order_price):
        order = {
            'symbol': self.bot.symbol.name,
            'side': 'BUY' if psn_side == 'LONG' else 'SELL',
            'positionSide': psn_side,
            'type': 'LIMIT',
            'price': str(round(order_price, int(self.bot.symbol.priceScale))),
            'qty': str(get_quantity_from_price(self.bot, order_price, self.bot.amount_long / self.grid.grid_count)),
        }
        if Decimal(order['qty']) == 0 and self.bot.is_active is True:
            min_amount = (Decimal(self.bot.symbol.minOrderQty) * self.current_price / self.bot.leverage).quantize(
                Decimal(1), rounding=ROUND_UP) * self.grid.grid_count
            custom_user_bot_logging(self.bot,
                                    f'Недостаточный стартовый капитал для открытия ордера, требуется не менее {min_amount}')
            self.bot.is_active = False
            self.bot.save()

        custom_logging(self.bot, f'order: {order}')
        custom_logging(self.bot, f'priceScale: {int(self.bot.symbol.priceScale)}')
        return order

    def current_price_waiting(self):
        while not self.current_price:
            time.sleep(0.1)

    def send_tg_message(self, message):
        pre_message = f'Account: {self.account.name}\nBot: {self.bot.id}\nSymbol: {self.symbol}\n'
        message = pre_message + message
        send_telegram_message(
            self.tg_acc.chat_id,
            message=message,
        )

    def send_info_income_per_deal(self):
        pnl = get_pnl_by_time(bot=self.bot, start_time=self.last_deal_time, end_time=timezone.now())
        pnl = round(Decimal(pnl), 5)
        self.update_bots_pnl_and_refresh_bots_data(added_pnl=pnl)

        message = f'PNL за последнюю сделку составил: {pnl}'
        custom_user_bot_logging(self.bot, message)
        self.send_tg_message(message=message)

        self.last_deal_time = timezone.now()

    def update_bots_pnl_and_refresh_bots_data(self, added_pnl):
        current_pnl = self.bot.pnl
        new_pnl = current_pnl + added_pnl
        self.update_total_pnl(added_pnl)

        self.bot.pnl = new_pnl
        BotModel.objects.filter(pk=self.bot.pk).update(pnl=new_pnl)

    def bots_data_init(self):
        self.bots_data, created = BotsData.objects.get_or_create(bot=self.bot)

    def update_total_pnl(self, added_pnl):
        self.bots_data.total_pnl = self.bots_data.total_pnl + added_pnl
        self.bots_data.save()
