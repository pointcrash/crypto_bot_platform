import time

from api_2.api_aggregator import cancel_all_orders, get_position_inform, place_order
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
    bot.enabled_manually = False
    bot.save(update_fields=['is_active', 'enabled_manually'])

    # if bot.is_active:
    #     bot.is_active = False
    #     bot.save()
    #     time.sleep(3)

    if user:
        custom_logging(bot, f'Бот был деактивирован вручную пользователем "{user.username}"')


def drop_psn_for_terminate_bot(bot):
    psn_list = get_position_inform(bot=bot)
    for psn in psn_list:
        side = 'SELL' if psn['side'] == 'LONG' else 'BUY'
        qty = psn['qty']
        place_order(bot=bot, side=side, position_side=psn['side'], qty=qty, price=None, order_type='MARKET')


# def terminate_bot_with_cancel_orders(bot, user=None):
#     terminate_bot(bot, user)
#     cancel_all_orders(bot)


# def terminate_bot_with_cancel_orders_and_drop_positions(bot, user=None):
#     terminate_bot_with_cancel_orders(bot, user)
#     drop_psn(bot=bot)

