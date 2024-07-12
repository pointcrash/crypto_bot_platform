import logging

from django.core.cache import cache

from api_2.api_aggregator import change_position_mode, set_leverage
from bots.general_functions import custom_user_bot_logging


class WorkGridClass:
    def __init__(self, bot):
        self.bot = bot
        self.grid = bot.grid
        self.symbol = bot.symbol.name
        self.current_price = bot.symbol.name
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

    def place_limit_orders(self):
        for grid_number in range(self.grid.grid_count):
            order_price = self.current_price + self.price_step * grid_number
            if self.current_price > order_price:
                if self.current_price - order_price >= self.price_step:
                    pass
            elif self.current_price > order_price:
                if self.current_price - order_price >= self.price_step:
                    pass

    def get_limit_order_data(self, psn_side, order_price):
        order = {
            'symbol': self.bot.symbol.name,
            'side': 'BUY' if psn_side == 'SHORT' else 'SELL',
            'positionSide': psn_side,
            'type': 'LIMIT',
            'price': str(order_price),
            'qty': str(order_data_class.coin_sold_count.quantize(Decimal(self.symbol.qtyStep), rounding=ROUND_UP)),
        }
        self.reduce_order_list[side].append(order)
        return order

