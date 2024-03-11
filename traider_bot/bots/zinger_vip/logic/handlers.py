from decimal import Decimal


def zinger_vip_handler_wrapper(bb_worker_class_obj):
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


def handle_message_kline_info(msg, bot_class_obj):
    pass


def handle_position_stream_message(msg, bot_class_obj):
    pass


def handle_order_stream_message(msg, bot_class_obj):
    pass


def handle_mark_price_stream_message(msg, bot_class_obj):
    print(msg)
    bot_class_obj.current_price = msg['markPrice']
