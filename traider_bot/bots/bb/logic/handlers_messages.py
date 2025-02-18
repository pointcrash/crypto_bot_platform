import logging
import time
from datetime import datetime
from decimal import Decimal

from api_2.api_aggregator import cancel_order
from api_2.custom_logging_api import custom_logging
from bots.general_functions import custom_user_bot_logging

bot_logger = logging.getLogger('bot_logger')


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
        with bot_class_obj.order_locker:
            if order_id in bot_class_obj.current_order_id:
                bot_class_obj.current_order_id.remove(order_id)
                custom_logging(bot_class_obj.bot, f' ORDER FILLED ID {order_id}')

                if order_id == bot_class_obj.open_order_id:
                    custom_user_bot_logging(bot_class_obj.bot, f' Открывающий ордер исполнен. ID: {order_id}')
                    bot_class_obj.send_tg_message(message=f'Открывающий ордер исполнен. ID: {order_id}')
                    pass
                    # bot_class_obj.bot_cycle_time_start_update()

                elif order_id == bot_class_obj.ml_order_id:
                    custom_user_bot_logging(bot_class_obj.bot,
                                            f' Выход на центральной линии. Ордер исполнен. ID: {order_id}')
                    bot_class_obj.send_tg_message(message=f'Выход на центральной линии. Ордер исполнен. ID: {order_id}')
                    bot_class_obj.send_info_income_per_deal()

                elif order_id == bot_class_obj.close_psn_main_order_id:
                    custom_user_bot_logging(bot_class_obj.bot, f' Закрывающий ордер исполнен. ID: {order_id}')
                    bot_class_obj.send_tg_message(message=f'Позиция закрыта, цикл завершен.')
                    bot_class_obj.send_info_income_per_deal()
                    cancel_order(bot_class_obj.bot, bot_class_obj.sl_order)
                    bot_class_obj.sl_order = None

                    if bot_class_obj.bot.bb.endless_cycle is False:
                        bot_class_obj.bot.is_active = False
                        bot_class_obj.bot.save()

                    # time.sleep(1)
                    # bot_class_obj.calc_and_save_pnl_per_cycle()

            else:
                if order_id == bot_class_obj.sl_order:
                    bot_class_obj.deactivate_bot()
                    custom_logging(bot_class_obj.bot, f' EXIT WITH STOP LOSS {order_id}')
                    custom_user_bot_logging(bot_class_obj.bot, f' Стоп лосс ордер исполнен. ID: {order_id}')

                    # time.sleep(1)
                    # bot_class_obj.calc_and_save_pnl_per_cycle()
                else:
                    # if msg['reduceOnly'] is True and Decimal(msg['qty']) >= bot_class_obj.position_info['qty']:
                    #     pass

                    custom_logging(bot_class_obj.bot, f' UNKNOWN ORDER FILLED ID {order_id}, params: {msg}')
                    custom_user_bot_logging(bot_class_obj.bot, f' Неизвестный ордер исполнен. ID: {order_id}')
                    bot_class_obj.send_tg_message(message=f'Неизвестный ордер исполнен. ID: {order_id}')


def handle_position_stream_message(msg, bot_class_obj):
    bot_logger.debug(msg)

    with bot_class_obj.psn_locker:
        msg_qty = Decimal(msg['qty'])

        if bot_class_obj.position_info.get('qty') == msg_qty:
            return

        if msg_qty != 0:
            if not bot_class_obj.position_info.get('qty'):
                custom_user_bot_logging(bot_class_obj.bot, f' Начало цикла: {datetime.now()}')
                bot_class_obj.bot_cycle_time_start_update()

            bot_class_obj.position_info = {
                'side': msg['side'],
                'qty': abs(msg_qty),
                'entryPrice': Decimal(msg['entryPrice']),
            }
            with bot_class_obj.avg_locker:
                bot_class_obj.avg_obj.update_psn_info(bot_class_obj.position_info)
            bot_class_obj.have_psn = True
            # bot_class_obj.cached_data(key='positionInfo', value=bot_class_obj.position_info)

        else:
            if msg['side'] == bot_class_obj.position_info.get('side'):
                bot_class_obj.position_info['qty'] = 0
                bot_class_obj.have_psn = False
                bot_class_obj.ml_filled = False
                bot_class_obj.ml_qty = 0
                bot_class_obj.ml_status_save()

                # bot_class_obj.cached_data(key='positionInfo', value=bot_class_obj.position_info)

                time.sleep(1)
                bot_class_obj.calc_and_save_pnl_per_cycle()
        # bot_class_obj.replace_closing_orders()


def handle_message_kline_info(msg, bot_class_obj):
    with bot_class_obj.psn_locker:
        close_prise = Decimal(msg['closePrice'])
        bot_class_obj.bb.modify_close_price_list(close_prise)
        bot_class_obj.bb.recalculate_lines()
        # bot_class_obj.cached_data(key='tl', value=bot_class_obj.bb.tl)
        # bot_class_obj.cached_data(key='ml', value=bot_class_obj.bb.ml)
        # bot_class_obj.cached_data(key='bl', value=bot_class_obj.bb.bl)
        # bot_class_obj.cached_data(key='closePriceList', value=bot_class_obj.bb.close_price_list)
        # if not bot_class_obj.have_psn:
        #     bot_class_obj.replace_opening_orders()
        # else:
        #     bot_class_obj.replace_closing_orders()


def handle_mark_price_stream_message(msg, bot_class_obj):
    # start_time = time.time()
    with bot_class_obj.order_locker:
        bot_class_obj.current_price = Decimal(msg['markPrice'])
        # bot_class_obj.cached_data(key='currentPrice', value=bot_class_obj.current_price)
        if not bot_class_obj.current_order_id:
            if bot_class_obj.have_psn is True:
                with bot_class_obj.avg_locker:
                    if bot_class_obj.avg_obj.auto_avg(bot_class_obj.current_price):
                        bot_class_obj.average()
                bot_class_obj.place_stop_loss()
                bot_class_obj.place_closing_orders()
                bot_class_obj.turn_after_ml()
            else:
                with bot_class_obj.psn_locker:
                    bot_class_obj.place_open_psn_order(bot_class_obj.current_price)

    # end_time = time.time()
    # execution_time = end_time - start_time
    # bot_class_obj.logger.debug(execution_time)
