from decimal import Decimal


def bb_handler_wrapper(bb_worker_class_obj):
    def bb_handle_stream_callback(message):
        if message['symbol'] == bb_worker_class_obj.symbol:
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
    print(msg)
    print()
    # if msg['symbol'] == bot_class_obj.symbol:
    if msg['status'].upper() == 'FILLED':
        if msg['orderId'] == bot_class_obj.ml_order_id:
            bot_class_obj.ml_filled = True
        elif msg['orderId'] == bot_class_obj.main_order_id:
            bot_class_obj.have_psn = False
            bot_class_obj.position_info = None
            bot_class_obj.ml_filled = False
            bot_class_obj.replace_opening_orders()


def handle_position_stream_message(msg, bot_class_obj):
    print(msg)
    print()
    # if msg['symbol'] == bot_class_obj.symbol:
    with bot_class_obj.locker_1:
        if Decimal(msg['qty']) != 0:
            if bot_class_obj.position_info:
                if bot_class_obj.position_info['qty'] == Decimal(msg['qty']):
                    return
            bot_class_obj.position_info = {
                'side': msg['side'],
                'qty': Decimal(msg['qty']),
                'entryPrice': Decimal(msg['entryPrice']),
            }
            with bot_class_obj.avg_locker:
                bot_class_obj.avg_obj.update_psn_info(bot_class_obj.position_info)
            bot_class_obj.have_psn = True
            bot_class_obj.replace_closing_orders()


def handle_message_kline_info(msg, bot_class_obj):
    print(msg)
    print()
    with bot_class_obj.locker_1:
        close_prise = Decimal(msg['closePrice'])
        bot_class_obj.bb.modify_close_price_list(close_prise)
        bot_class_obj.bb.recalculate_lines()
        if not bot_class_obj.have_psn:
            bot_class_obj.replace_opening_orders()
        else:
            bot_class_obj.replace_closing_orders()


def handle_mark_price_stream_message(msg, bot_class_obj):
    # print(msg)
    # print()
    bot_class_obj.current_price = Decimal(msg['markPrice'])
    if bot_class_obj.have_psn is True:
        with bot_class_obj.avg_locker:
            bot_class_obj.avg_obj.auto_avg(bot_class_obj.current_price)
