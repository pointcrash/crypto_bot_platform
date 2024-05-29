import threading
import time
from decimal import Decimal

from api_2.custom_logging_api import custom_logging

market_price_locker = threading.Lock()


def zinger_handler_wrapper_market(bb_worker_class_obj):
    def bb_handle_stream_callback(message):
        if message['topic'] == 'position':
            handle_position_stream_message(message, bb_worker_class_obj)

        elif message['topic'] == 'order':
            handle_order_stream_message(message, bb_worker_class_obj)

        elif message['topic'] == 'markPrice':
            handle_mark_price_stream_message(message, bb_worker_class_obj)

        else:
            pass

    return bb_handle_stream_callback


def handle_order_stream_message(msg, bot_class_obj):
    with bot_class_obj.order_locker:
        if msg['status'] == 'FILLED':
            psn_side = msg['psnSide']
            psn_price = Decimal(msg['avgPrice'])
            psn_qty = Decimal(msg['qty'])

            if msg['orderId'] == bot_class_obj.open_order_id_list.get(psn_side):
                custom_logging(bot_class_obj.bot, f'OPEN ORDER {msg["orderId"]} {msg["status"]}')
                bot_class_obj.place_tp_orders(psn_side, psn_price, psn_qty)

            elif msg['orderId'] == bot_class_obj.tp_order_id_list.get(psn_side):
                custom_logging(bot_class_obj.bot, f'TP ORDER {msg["orderId"]} {msg["status"]}')
                bot_class_obj.update_realized_pnl(psn_side=psn_side)
                bot_class_obj.reinvest(psn_side=psn_side)
                if bot_class_obj.zinger.is_nipple_active:
                    bot_class_obj.nipple_side = psn_side
                    bot_class_obj.calc_second_open_order_price_by_nipple(psn_side, psn_qty, psn_price)
                else:
                    bot_class_obj.place_second_open_order(psn_side, psn_qty)

            elif msg['orderId'] == bot_class_obj.end_order_id_list.get(psn_side):
                custom_logging(bot_class_obj.bot, f'END CYCLE ORDER {msg["orderId"]} {msg["status"]}')

            else:
                custom_logging(bot_class_obj.bot, f'UNKNOWN ORDER {msg["orderId"]} {msg["status"]}')
                bot_class_obj.replace_tp_order(psn_side, psn_price, psn_qty)
        else:
            custom_logging(bot_class_obj.bot, f'UNKNOWN ORDER {msg["orderId"]} {msg["status"]}')


def handle_position_stream_message(msg, bot_class_obj):
    psn_side = msg['side']
    if psn_side:
        bot_class_obj.position_info[psn_side] = {
            'qty': abs(Decimal(msg['qty'])),
            'entryPrice': Decimal(msg['entryPrice']),
            'unrealisedPnl': Decimal(msg['unrealisedPnl']),
        }
        bot_class_obj.cached_data(key='positionInfo', value=bot_class_obj.position_info)


def handle_mark_price_stream_message(msg, bot_class_obj):
    with market_price_locker:
        bot_class_obj.current_price = Decimal(msg['markPrice'])
        bot_class_obj.cached_data(key='currentPrice', value=msg['markPrice'])

        with bot_class_obj.tp_trailing_data_locker:
            for psn_side in bot_class_obj.tp_trailing_data:
                if bot_class_obj.activate_trailing_check(psn_side) is True:
                    bot_class_obj.trailing_order(psn_side)

        bot_class_obj.nipple()

        current_pnl = bot_class_obj.calc_pnl()
        if current_pnl > bot_class_obj.required_income:
            bot_class_obj.end_cycle(current_pnl)
