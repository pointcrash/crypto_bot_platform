import time

from api_2.api_aggregator import cancel_all_orders
from bots.general_functions import custom_logging


def terminate_thread(bot_id, keep_active=False):
    pass


def check_thread_alive(bot_id):
    pass


def drop_position(bot):
    pass


def stop_bot_with_cancel_orders(bot):
    pass


def stop_bot_with_cancel_orders_and_drop_positions(bot):
    pass


def terminate_bot(bot, user=None):
    bot.is_active = False
    bot.save()
    time.sleep(7)

    if user:
        custom_logging(bot, f'Бот был деактивирован вручную пользователем "{user.username}"')


def terminate_bot_with_cancel_orders(bot, user=None):
    terminate_bot(bot, user)
    cancel_all_orders(bot)


def terminate_bot_with_cancel_orders_and_drop_positions(bot, user=None):
    terminate_bot_with_cancel_orders(bot, user)

