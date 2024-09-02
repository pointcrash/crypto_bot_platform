import logging
import time
from decimal import Decimal

from binance.exceptions import BinanceAPIException
from django.core.cache import cache

from api_2.api_aggregator import change_position_mode, set_leverage, get_quantity_from_price, place_batch_order, \
    place_order
from bots.general_functions import custom_user_bot_logging, custom_logging


class WorkGridClass:
    def __init__(self, bot):
        self.bot = bot
        self.grid = bot.grid
        self.symbol = bot.symbol.name
        self.current_price = None
        self.price_step = self.get_price_step()

        self.logger = self.get_logger_for_bot_ws_msg(bot.id)

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

        custom_logging(self.bot, f'order: {order}')
        custom_logging(self.bot, f'priceScale: {int(self.bot.symbol.priceScale)}')
        return order

    def current_price_waiting(self):
        while not self.current_price:
            time.sleep(0.1)
