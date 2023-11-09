from decimal import Decimal


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
        last_price = Decimal(message['data']['lastPrice'])
        # print(last_price, step_class_obj.avg_trigger_price[1], step_class_obj.avg_trigger_price[2])
        # print(step_class_obj.class_data_obj.data)
        # if last_price <= Decimal(step_class_obj.class_data_obj.data['avg_trigger_price'][1]):
        if last_price <= step_class_obj.avg_trigger_price[1]:
            if not step_class_obj.class_data_obj.data['is_avg_psn_flag_dict'][1]:
                # print('average')
                # print(step_class_obj.class_data_obj.data)
                step_class_obj.class_data_obj.data['is_avg_psn_flag_dict'][1] = True
                # print(step_class_obj.class_data_obj.data)
                step_class_obj.class_data_obj.save()
                # print(step_class_obj.class_data_obj.data)
                step_class_obj.ws_average_psn_by_market(1)
        # if last_price >= Decimal(step_class_obj.class_data_obj.data['avg_trigger_price'][2]):
        if last_price >= step_class_obj.avg_trigger_price[2]:
            if not step_class_obj.class_data_obj.data['is_avg_psn_flag_dict'][2]:
                # print('average-2')
                # print(step_class_obj.class_data_obj.data)
                step_class_obj.class_data_obj.data['is_avg_psn_flag_dict'][2] = True
                # print(step_class_obj.class_data_obj.data)
                step_class_obj.class_data_obj.save()
                # print(step_class_obj.class_data_obj.data)
                step_class_obj.ws_average_psn_by_market(2)
    except Exception as e:
        print(e)


def handle_order_stream_message(message, step_class_obj):
    # print('--------------------START--ORDER-LIST----------------------')
    for order in message['data']:
        # print(order)
        if order['symbol'] == step_class_obj.symbol.name:
            if order['reduceOnly'] is False:
                if order['orderStatus'] == 'Filled':
                    if order['timeInForce'] == 'IOC':
                        if order['stopOrderType'] == 'Stop':
                            if order['orderId'] == step_class_obj.new_psn_orderId_dict[order['positionIdx']]:
                                step_class_obj.ws_place_tp_order(order)
                                step_class_obj.ws_place_new_psn_order(order)

                    # elif order['timeInForce'] == 'GTC':
                    #     step_class_obj.is_avg_psn_flag_dict[order['positionIdx']] = True

                elif order['orderStatus'] == 'Untriggered':
                    step_class_obj.new_psn_orderId_dict[order['positionIdx']] = order['orderId']

                # elif order['orderStatus'] == 'New':
                #     if order['timeInForce'] == 'GTC':
                #         step_class_obj.avg_order_id[order['positionIdx']] = order['orderId']

    # print('--------------------END--ORDER-LIST------------------------')
    # print()


def handle_position_stream_message(message, step_class_obj):
    # print('--------------------START--POSITION-LIST----------------------')
    for psn in message['data']:
        # print(psn)
        if psn['symbol'] == step_class_obj.symbol.name:
            position_idx = psn['positionIdx']
            try:
                if psn['entryPrice'] != step_class_obj.ws_symbol_list[position_idx]['entryPrice']:
                    step_class_obj.ws_symbol_list[position_idx] = psn
                    step_class_obj.calculate_avg_trigger_price(position_idx)

                    step_class_obj.class_data_obj.data['is_avg_psn_flag_dict'][position_idx] = False
                    step_class_obj.class_data_obj.save()

                    step_class_obj.ws_amend_tp_order(position_idx)
                    step_class_obj.ws_amend_new_psn_order(position_idx)
            except Exception as e:
                try:
                    step_class_obj.ws_symbol_list[position_idx] = psn
                    step_class_obj.calculate_avg_trigger_price(position_idx)
                except:
                    pass
                # print(e)

    # print('--------------------END--POSITION-LIST------------------------')
    # print()


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
