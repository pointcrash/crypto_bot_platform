import logging
import time
from datetime import datetime
from decimal import Decimal

from api_2.api_aggregator import cancel_order
from api_2.custom_logging_api import custom_logging
from bots.general_functions import custom_user_bot_logging


def grid_handler_wrapper(bb_worker_class_obj):
    def bb_handle_stream_callback(message):
        if message['topic'] == 'position':
            handle_position_stream_message(message, bb_worker_class_obj)

        elif message['topic'] == 'order':
            handle_order_stream_message(message, bb_worker_class_obj)

        elif message['topic'] == 'markPrice':
            handle_mark_price_stream_message(message, bb_worker_class_obj)

        elif message['topic'] == 'kline':
            handle_message_kline_info(message, bb_worker_class_obj)

        else:
            pass

    return bb_handle_stream_callback


def handle_order_stream_message(msg, bot_class_obj):
    custom_logging(bot_class_obj.bot, f'ORDER {msg}')
    order_id = msg['orderId']

    if msg['status'].upper() == 'FILLED':
        if not msg['reduceOnly']:
            custom_user_bot_logging(bot_class_obj.bot, f' Открывающий ордер исполнен. ID: {order_id}')
            bot_class_obj.send_tg_message(message=f'Открывающий ордер исполнен. ID: {order_id}')

            bot_class_obj.place_close_order(psn_side=msg['psnSide'], price=msg['price'], qty=msg['qty'])
        else:
            custom_user_bot_logging(bot_class_obj.bot, f' Закрывающий ордер исполнен. ID: {order_id}')
            bot_class_obj.send_tg_message(message=f'Закрывающий ордер исполнен. ID: {order_id}')
            bot_class_obj.send_info_income_per_deal()

            bot_class_obj.place_new_open_order(psn_side=msg['psnSide'], price=msg['price'], qty=msg['qty'])


def handle_position_stream_message(msg, bot_class_obj):
    custom_logging(bot_class_obj.bot, f'POSITION {msg}')


def handle_message_kline_info(msg, bot_class_obj):
    pass


def handle_mark_price_stream_message(msg, bot_class_obj):
    bot_class_obj.current_price = Decimal(msg['markPrice'])
