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
    print(msg)
    # print()
    # with bot_class_obj.locker_1:
    #     if msg['symbol'] == bot_class_obj.symbol:
    #         if Decimal(msg['qty']) != 0:
    #             if bot_class_obj.position_info:
    #                 if bot_class_obj.position_info['qty'] == Decimal(msg['qty']):
    #                     return
    #             bot_class_obj.position_info = {
    #                 'side': msg['side'],
    #                 'qty': Decimal(msg['qty']),
    #                 'entryPrice': Decimal(msg['entryPrice']),
    #             }
    #             with bot_class_obj.avg_locker:
    #                 bot_class_obj.avg_obj.update_psn_info(bot_class_obj.position_info)
    #             bot_class_obj.have_psn = True
    #             bot_class_obj.replace_closing_orders()
    #         else:
    #             if bot_class_obj.position_info:
    #                 if msg['side'] == bot_class_obj.position_info['side']:
    #                     bot_class_obj.have_psn = False
    #                     bot_class_obj.position_info = None
    #                     bot_class_obj.replace_opening_orders()


def handle_order_stream_message(msg, bot_class_obj):
    print(msg)
    if msg['status'].upper() == 'FILLED':
        side = msg['psnSide']
        bot_class_obj.position_info[side] = {
            'side': side,
            'qty': Decimal(msg['qty']),
            'entryPrice': Decimal(msg['avgPrice']),
        }
        bot_class_obj.place_reduction_orders()


def handle_mark_price_stream_message(msg, bot_class_obj):
    # print(msg)
    bot_class_obj.current_price = msg['markPrice']
