import logging
import time
from decimal import Decimal

from api_2.custom_logging_api import custom_logging


def bb_handler_wrapper(bb_worker_class_obj):
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
    if msg['status'].upper() == 'FILLED':
        order_id = msg['orderId']
        if order_id == bot_class_obj.current_order_id:
            bot_class_obj.current_order_id = ''
            custom_logging(bot_class_obj.bot, f' ORDER FILLED ID {order_id}')
        else:
            custom_logging(bot_class_obj.bot, f' CUSTOM ORDER FILLED ID {order_id}')
    #     if msg['orderId'] == bot_class_obj.ml_order_id:
    #         bot_class_obj.ml_filled = True
    #     elif msg['orderId'] == bot_class_obj.main_order_id:
    #         bot_class_obj.have_psn = False
    #         bot_class_obj.position_info = None
    #         bot_class_obj.ml_filled = False
    #         bot_class_obj.replace_opening_orders()


def handle_position_stream_message(msg, bot_class_obj):
    with bot_class_obj.psn_locker:
        if Decimal(msg['qty']) != 0:
            if bot_class_obj.position_info.get('qty') == Decimal(msg['qty']):
                return
            bot_class_obj.position_info = {
                'side': msg['side'],
                'qty': abs(Decimal(msg['qty'])),
                'entryPrice': Decimal(msg['entryPrice']),
            }
            with bot_class_obj.avg_locker:
                bot_class_obj.avg_obj.update_psn_info(bot_class_obj.position_info)
            bot_class_obj.have_psn = True
        else:
            if msg['side'] == bot_class_obj.position_info['side']:
                bot_class_obj.position_info['qty'] = 0
                bot_class_obj.have_psn = False
        bot_class_obj.cached_data(key='positionInfo', value=bot_class_obj.position_info)

        # bot_class_obj.replace_closing_orders()


def handle_message_kline_info(msg, bot_class_obj):
    with bot_class_obj.psn_locker:
        close_prise = Decimal(msg['closePrice'])
        bot_class_obj.bb.modify_close_price_list(close_prise)
        bot_class_obj.bb.recalculate_lines()
        bot_class_obj.cached_data(key='tl', value=bot_class_obj.bb.tl)
        bot_class_obj.cached_data(key='ml', value=bot_class_obj.bb.ml)
        bot_class_obj.cached_data(key='bl', value=bot_class_obj.bb.bl)
        bot_class_obj.cached_data(key='closePriceList', value=bot_class_obj.bb.close_price_list)
        # if not bot_class_obj.have_psn:
        #     bot_class_obj.replace_opening_orders()
        # else:
        #     bot_class_obj.replace_closing_orders()


def handle_mark_price_stream_message(msg, bot_class_obj):
    start_time = time.time()

    bot_class_obj.current_price = Decimal(msg['markPrice'])
    bot_class_obj.cached_data(key='currentPrice', value=bot_class_obj.current_price)
    if not bot_class_obj.current_order_id:
        if bot_class_obj.have_psn is True:
            with bot_class_obj.avg_locker:
                if bot_class_obj.avg_obj.auto_avg(bot_class_obj.current_price):
                    bot_class_obj.ml_filled = False
                    bot_class_obj.ml_qty = 0
            bot_class_obj.place_closing_orders()
            bot_class_obj.turn_after_ml()
        else:
            with bot_class_obj.psn_locker:
                bot_class_obj.place_open_psn_order(bot_class_obj.current_price)

    end_time = time.time()
    execution_time = end_time - start_time
    bot_class_obj.logger.debug(execution_time)

# def handle_mark_price_stream_message(msg, bot_class_obj):
#     bot_class_obj.current_price = Decimal(msg['markPrice'])
#     if bot_class_obj.have_psn is True:
#         with bot_class_obj.avg_locker:
#             bot_class_obj.avg_obj.auto_avg(bot_class_obj.current_price)
