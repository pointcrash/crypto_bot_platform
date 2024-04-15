from decimal import Decimal

from api_2.custom_logging_api import custom_logging


def zinger_handler_wrapper(bb_worker_class_obj):
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
        custom_logging(bot_class_obj.bot, f'ORDER {msg["orderId"]} {msg["status"]}')

        if msg['status'] == 'FILLED':
            psn_side = msg['psnSide']
            psn_price = Decimal(msg['avgPrice'])
            psn_qty = Decimal(msg['qty'])

            if msg['orderId'] == bot_class_obj.open_order_id_list[psn_side]:
                bot_class_obj.place_tp_orders(psn_side, psn_price, psn_qty)

            elif msg['orderId'] == bot_class_obj.tp_order_id_list[psn_side]:
                bot_class_obj.nipple_side = psn_side
                bot_class_obj.realizedPnl += bot_class_obj.unrealizedPnl[psn_side]
                bot_class_obj.place_second_open_order(psn_side, psn_qty)


def handle_position_stream_message(msg, bot_class_obj):
    psn_side = msg['side']
    if psn_side:
        bot_class_obj.position_info[psn_side] = {
            'qty': abs(Decimal(msg['qty'])),
            'entryPrice': Decimal(msg['entryPrice']),
            'unrealisedPnl': Decimal(msg['unrealisedPnl']),
        }


def handle_mark_price_stream_message(msg, bot_class_obj):
    bot_class_obj.current_price = Decimal(msg['markPrice'])
    current_pnl = bot_class_obj.calc_pnl()
    if current_pnl > bot_class_obj.income:
        bot_class_obj.end_cycle(current_pnl)
