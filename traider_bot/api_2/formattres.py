def order_formatters(order):
    formated_order = {'symbol': order['symbol'], 'orderId': order['orderId'], 'price': order['price']}

    #  status
    if order.get('orderStatus'):
        formated_order['status'] = order['orderStatus']
    elif order.get('status'):
        formated_order['status'] = order['status']
    else:
        formated_order['status'] = ''

    #  clientOrderId
    if order.get('clientOrderId'):
        formated_order['clientOrderId'] = order['clientOrderId']
    elif order.get('orderLinkId'):
        formated_order['clientOrderId'] = order['orderLinkId']
    else:
        formated_order['clientOrderId'] = ''

    #  orderType
    if order.get('origType'):
        formated_order['orderType'] = order['origType']
    elif order.get('orderType'):
        formated_order['orderType'] = order['orderType']
    else:
        formated_order['orderType'] = ''

    #  triggerPrice
    if order.get('stopPrice'):
        formated_order['triggerPrice'] = order['stopPrice']
    elif order.get('triggerPrice'):
        formated_order['triggerPrice'] = order['triggerPrice']
    else:
        formated_order['triggerPrice'] = ''

    #  qty
    if order.get('origQty'):
        formated_order['qty'] = order['origQty']
    elif order.get('qty'):
        formated_order['qty'] = order['qty']
    else:
        formated_order['qty'] = ''

    #  side
    if order.get('side'):
        formated_order['side'] = order['side'].upper()
    else:
        formated_order['side'] = ''

    #  psnSide
    if order.get('positionSide'):
        formated_order['psnSide'] = order['positionSide']
    elif order.get('positionIdx'):
        formated_order['psnSide'] = 'LONG' if order['positionIdx'] == 1 else 'SHORT'
    else:
        formated_order['psnSide'] = ''

    #  reduceOnly
    if order.get('reduceOnly'):
        formated_order['reduceOnly'] = order['reduceOnly']
    else:
        formated_order['reduceOnly'] = ''

    formated_order = open_close_format(formated_order)

    return formated_order


def open_close_format(order):
    if order['psnSide'] == 'LONG':
        if order['side'] == 'BUY':
            order['side'] = 'OPEN'
        elif order['side'] == 'SELL':
            order['side'] = 'CLOSE'

    elif order['psnSide'] == 'SHORT':
        if order['side'] == 'BUY':
            order['side'] = 'CLOSE'
        elif order['side'] == 'SELL':
            order['side'] = 'OPEN'

    return order
