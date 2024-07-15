import logging
import time

from django.core.cache import cache

from api_2.api_aggregator import change_position_mode, set_leverage, get_quantity_from_price, place_batch_order
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
        return self.grid.high_price - self.grid.low_price / self.grid.grid_count

    def initial_placing_orders(self):
        order_list = self.get_order_list()
        response = place_batch_order(self.bot, order_list=order_list)
        custom_logging(self.bot, f'place batch orders: {order_list}')
        custom_logging(self.bot, f'place batch orders response: {response}')

    def get_order_list(self):
        self.current_price_waiting()

        order_list = []
        for grid_number in range(self.grid.grid_count):
            order = None
            order_price = self.current_price + self.price_step * grid_number
            if self.current_price > order_price:
                if self.current_price - order_price >= self.price_step:
                    order = self.get_limit_order_data(psn_side='LONG', order_price=order_price, action_type='OPEN')

            elif self.current_price > order_price:
                if self.current_price - order_price >= self.price_step:
                    order = self.get_limit_order_data(psn_side='SHORT', order_price=order_price, action_type='OPEN')

            if not order:
                continue

            order_list.append(order)
        return order_list

    def get_limit_order_data(self, psn_side, order_price, action_type='OPEN'):
        order = {
            'symbol': self.bot.symbol.name,
            'positionSide': psn_side,
            'type': 'LIMIT',
            'price': str(order_price),
            'qty': get_quantity_from_price(self.bot, order_price, self.bot.amount_long),
        }
        if action_type == 'OPEN':
            order['side'] = 'BUY' if psn_side == 'LONG' else 'SELL'
        elif action_type == 'CLOSE':
            order['side'] = 'SELL' if psn_side == 'LONG' else 'BUY'
        else:
            raise ValueError('"order_price" value is incorrect, must be "CLOSE" or "OPEN"')
        return order

    def current_price_waiting(self):
        while not self.current_price:
            time.sleep(0.1)

