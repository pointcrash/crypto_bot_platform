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
    if msg['symbol'] == bot_class_obj.symbol_name:
        with bot_class_obj.psn_locker:
            if Decimal(msg['qty']) != 0:
                if bot_class_obj.position_info:
                    if bot_class_obj.position_info[msg['side']]['qty'] == Decimal(msg['qty']):
                        return
                bot_class_obj.position_info[msg['side']] = {
                    'side': msg['side'],
                    'qty': Decimal(msg['qty']),
                    'entryPrice': Decimal(msg['entryPrice']),
                    'realisedPnl': Decimal(msg['realisedPnl']),
                }

                #  Рассчитываем цену выхода из цикла
                end_cycle_price = bot_class_obj.calc_end_cycle_price()
                if end_cycle_price:
                    print(end_cycle_price)


def handle_order_stream_message(msg, bot_class_obj):
    print()
    print(msg)
    if msg['status'].upper() == 'FILLED':
        side = msg['psnSide']
        if msg['orderId'] in bot_class_obj.reduce_order_id_list[side]:
            index = bot_class_obj.reduce_order_id_list[side].index(msg['orderId'])
            if index != 0:
                raise Exception(f'Исполненный ордер нарушает очередь. Место в списке {index}')
            bot_class_obj.count_reduce_order_filled[side] += 1
            bot_class_obj.reduce_order_id_list[side].pop(index)
            bot_class_obj.place_next_reduction_order(side=side)


def handle_mark_price_stream_message(msg, bot_class_obj):
    print(msg)
    bot_class_obj.current_price = msg['markPrice']
