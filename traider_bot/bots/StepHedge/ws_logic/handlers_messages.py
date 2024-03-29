from decimal import Decimal

from bots.general_functions import custom_logging


# def callback_func_choices(step_class_obj, topic,  message):
#     if topic == 'position':
#         handle_position_stream_message(message, step_class_obj)
#     elif topic == 'order':
#         handle_order_stream_message(message, step_class_obj)
#     elif topic == 'tickers':
#         handle_ticker_stream_message(message, step_class_obj)
#     else:
#         raise ValueError(f'Invalid argument {topic}')


def handle_stream_callback(step_class_obj, arg):
    if arg == 'position':
        def callback(message):
            handle_position_stream_message(message, step_class_obj)
    elif arg == 'order':
        def callback(message):
            handle_order_stream_message(message, step_class_obj)
    elif arg == 'ticker':
        def callback(message):
            handle_ticker_stream_message(message, step_class_obj)
    else:
        raise ValueError(f'Invalid argument {arg}')

    return callback


def handle_ticker_stream_message(message, step_class_obj):
    try:
        if 'lastPrice' in message['data']:
            last_price = Decimal(message['data']['lastPrice'])
            if step_class_obj.last_price != last_price:
                with step_class_obj.locker_1:
                    step_class_obj.last_price = last_price
                    move_nipple = step_class_obj.step_hg.move_nipple

                    # missed_order_psn_idx = step_class_obj.order_missed_check(last_price)
                    # if missed_order_psn_idx:
                    #     step_class_obj.buy(missed_order_psn_idx, last_price)

                    # Ниппель, усреднение
                    if step_class_obj.long1invest:
                        position_idx = 1
                        if move_nipple and step_class_obj.tp_order_executed[position_idx]:
                            if step_class_obj.new_psn_price_dict[position_idx] - last_price > step_class_obj.qty_steps * step_class_obj.tickSize:
                                step_class_obj.new_psn_price_dict[position_idx] -= step_class_obj.qty_steps_diff * step_class_obj.tickSize
                                step_class_obj.ws_amend_new_psn_order(position_idx)
                        if last_price <= step_class_obj.avg_trigger_price[position_idx]:
                            ws_average_actions_for_step_hedge(step_class_obj, position_idx)

                    if step_class_obj.short1invest:
                        position_idx = 2
                        if move_nipple and step_class_obj.tp_order_executed[position_idx]:
                            if last_price - step_class_obj.new_psn_price_dict[position_idx] > step_class_obj.qty_steps * step_class_obj.tickSize:
                                step_class_obj.new_psn_price_dict[position_idx] += step_class_obj.qty_steps_diff * step_class_obj.tickSize
                                step_class_obj.ws_amend_new_psn_order(position_idx)
                        if last_price >= step_class_obj.avg_trigger_price[position_idx]:
                            ws_average_actions_for_step_hedge(step_class_obj, position_idx)

                    # Усреднение
                    # if step_class_obj.long1invest:
                    #     if last_price <= step_class_obj.avg_trigger_price[1]:
                    #         ws_average_actions_for_step_hedge(step_class_obj, 1)
                    # if step_class_obj.short1invest:
                    #     if last_price >= step_class_obj.avg_trigger_price[2]:
                    #         ws_average_actions_for_step_hedge(step_class_obj, 2)

    except Exception as e:
        print('Exception in tickers func: ', e)


def handle_order_stream_message(message, step_class_obj):
    with step_class_obj.locker_2:
        try:
            # print('--------------------START--ORDER-LIST----------------------')
            for order in message['data']:
                if order['symbol'] == step_class_obj.symbol.name:
                    if order['reduceOnly'] is False:
                        if order['orderStatus'] == 'Filled':
                            if order['timeInForce'] == 'IOC':
                                if order['stopOrderType'] == 'Stop':
                                    if order['orderId'] == step_class_obj.new_psn_orderId_dict[order['positionIdx']]:
                                        if not step_class_obj.new_order_is_filled[order['positionIdx']]:
                                            step_class_obj.new_order_is_filled[order['positionIdx']] = True
                                            step_class_obj.tp_order_executed[order['positionIdx']] = False
                                            step_class_obj.ws_place_tp_order(order)
                                            step_class_obj.ws_place_new_psn_order(order)
                        elif order['orderStatus'] == 'Deactivated':
                            if order['cancelType'] == 'CancelByUser':
                                if order['orderId'] == step_class_obj.new_psn_orderId_dict[order['positionIdx']]:
                                    step_class_obj.ws_place_new_psn_order(order, status=order['orderStatus'])

                        elif order['orderStatus'] == 'Untriggered':
                            step_class_obj.new_psn_orderId_dict[order['positionIdx']] = order['orderId']
                            step_class_obj.new_order_is_filled[order['positionIdx']] = False
                            if step_class_obj.locker_3.locked():
                                step_class_obj.locker_3.release()

                        elif order['orderStatus'] == 'Triggered':
                            step_class_obj.locker_3.acquire()

                    elif order['reduceOnly'] is True:
                        if order['orderStatus'] == 'Filled':
                            step_class_obj.tp_order_executed[order['positionIdx']] = True
                        elif order['orderStatus'] == 'Deactivated':
                            step_class_obj.ws_place_tp_order(order, status=order['orderStatus'])

            # print('--------------------END--ORDER-LIST------------------------')
            # print()
        except Exception as e:
            print(f'ОШИБКА В КАЛБЕК ОРДЕРЕ {e}')
            custom_logging(step_class_obj.bot, f'ОШИБКА В КАЛБЕК ОРДЕРЕ {e}')
            raise ValueError('')


def handle_position_stream_message(message, step_class_obj):
    with step_class_obj.locker_2:
        # print('--------------------START--POSITION-LIST----------------------')
        for psn in message['data']:
            # print(psn)
            if psn['symbol'] == step_class_obj.symbol.name:
                position_idx = psn['positionIdx']
                try:
                    # if Decimal(psn['entryPrice']) != 0:
                    if psn['entryPrice'] != step_class_obj.ws_symbol_list[position_idx]['entryPrice']:
                        step_class_obj.ws_symbol_list[position_idx] = psn
                        step_class_obj.calculate_avg_trigger_price(position_idx)

                        step_class_obj.is_avg_psn_flag_dict[position_idx] = False

                        step_class_obj.ws_amend_tp_order(position_idx)
                        step_class_obj.ws_amend_new_psn_order(position_idx)
                except Exception as e:
                    try:
                        step_class_obj.ws_symbol_list[position_idx] = psn
                        step_class_obj.calculate_avg_trigger_price(position_idx)
                    except Exception as e:
                        print(e)

        # print('--------------------END--POSITION-LIST------------------------')
        # print()


def ws_average_actions_for_step_hedge(step_class_obj, position_idx):
    if float(step_class_obj.ws_symbol_list[position_idx]['size']):
        if not step_class_obj.is_avg_psn_flag_dict[position_idx]:
            step_class_obj.is_avg_psn_flag_dict[position_idx] = True
            step_class_obj.ws_average_psn_by_market(position_idx)


'''
    Limit open order parameters:
    {'category': 'linear', 'symbol': 'SANDUSDT', 'orderId': 'c2691c21-0b0d-49a7-9256-5ce0d9c3b473',
    'orderLinkId': '40ea011c18e9432e874df175c7055f15', 'blockTradeId': '', 'side': 'Buy', 'positionIdx': 1,
    'orderStatus': 'New', 'cancelType': 'UNKNOWN', 'rejectReason': 'EC_NoError', 'timeInForce': 'GTC',
    'isLeverage': '', 'price': '0.389', 'qty': '2566', 'avgPrice': '', 'leavesQty': '2566', 'leavesValue': '998.174',
    'cumExecQty': '0', 'cumExecValue': '0', 'cumExecFee': '0', 'orderType': 'Limit', 'stopOrderType': '', 'orderIv': '',
    'triggerPrice': '', 'takeProfit': '', 'stopLoss': '', 'triggerBy': '', 'tpTriggerBy': '', 'slTriggerBy': '',
    'triggerDirection': 0, 'placeType': '', 'lastPriceOnCreated': '0.3897', 'closeOnTrigger': False, 'reduceOnly': False,
    'smpGroup': 0, 'smpType': 'None', 'smpOrderId': '', 'slLimitPrice': '0', 'tpLimitPrice': '0', 'tpslMode': 'UNKNOWN',
    'createdTime': '1699279409295', 'updatedTime': '1699279409299', 'feeCurrency': ''}
'''



'''
{'category': 'linear', 'symbol': 'SANDUSDT', 'orderId': 'd2f1c5f4-578c-4ab0-ad23-0d58e1dca456',
 'orderLinkId': '9171ebfc9e64420294fafac27dfc7694', 'blockTradeId': '', 'side': 'Sell', 'positionIdx': 2,
 'orderStatus': 'Deactivated', 'cancelType': 'CancelByUser', 'rejectReason': 'EC_NoError', 'timeInForce': 'IOC',
 'isLeverage': '', 'price': '0', 'qty': '2287', 'avgPrice': '', 'leavesQty': '0', 'leavesValue': '0',
 'cumExecQty': '0', 'cumExecValue': '0', 'cumExecFee': '0', 'orderType': 'Market', 'stopOrderType': 'Stop',
 'orderIv': '', 'triggerPrice': '0.4371', 'takeProfit': '', 'stopLoss': '', 'triggerBy': 'LastPrice',
 'tpTriggerBy': '', 'slTriggerBy': '', 'triggerDirection': 2, 'placeType': '', 'lastPriceOnCreated': '0.4423',
 'closeOnTrigger': False, 'reduceOnly': False, 'smpGroup': 0, 'smpType': 'None', 'smpOrderId': '', 'slLimitPrice': '0',
 'tpLimitPrice': '0', 'tpslMode': 'UNKNOWN', 'createdTime': '1701794440765', 'updatedTime': '1701794479238', 'feeCurrency': ''}
'''