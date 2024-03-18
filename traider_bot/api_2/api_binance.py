from decimal import Decimal
from functools import wraps
from binance.client import Client


def sort_position_inform(unsorted_list):
    sorted_list = sorted(unsorted_list, key=lambda x: x['side'])
    return sorted_list


def with_binance_client(func):
    @wraps(func)
    def wrapper(bot, *args, **kwargs):
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=not bot.account.is_mainnet)
        return func(bot, client, *args, **kwargs)

    return wrapper


@with_binance_client
def binance_get_position_inform(bot, client):
    def format_data(position_list):
        position_inform_list = [{
            'symbol': position['symbol'],
            'qty': position['positionAmt'],
            'entryPrice': position['entryPrice'],
            'markPrice': position['markPrice'],
            'unrealisedPnl': position['unRealizedProfit'],
            'side': position['positionSide'],
        } for position in position_list]

        return sort_position_inform(position_inform_list)

    response = client.futures_position_information(symbol=bot.symbol.name)
    position_inform_list = format_data(response)
    return position_inform_list


@with_binance_client
def binance_place_order(bot, client, side, order_type, price, qty, position_side, timeInForce='GTC'):
    if order_type.capitalize() == 'Market':
        price = None
    if not position_side:
        position_side = 'LONG' if side.lower() == 'buy' else 'SHORT'
    return client.futures_create_order(
        symbol=bot.symbol.name,
        side=side.upper(),
        positionSide=position_side,
        type=order_type.upper(),
        price=price,
        timeInForce=timeInForce,
        quantity=qty,
    )


@with_binance_client
def binance_place_batch_order(bot, client, order_list):
    for order in order_list:
        if not order.get('timeInForce') and order.get('type') == 'LIMIT':
            order['timeInForce'] = 'GTC'
        order['quantity'] = order.pop('qty')

    response = client.futures_place_batch_order(batchOrders=order_list)
    return response


@with_binance_client
def binance_cancel_all_orders(bot, client):
    response = client.futures_cancel_all_open_orders(symbol=bot.symbol.name)
    return response


@with_binance_client
def binance_cancel_order(bot, client, order_id):
    response = client.futures_cancel_order(symbol=bot.symbol.name, orderId=order_id)
    return response


@with_binance_client
def binance_get_open_orders(bot, client):
    response = client.futures_get_open_orders(symbol=bot.symbol.name)
    return response


@with_binance_client
def binance_get_current_price(bot, client):
    response = client.futures_symbol_ticker(symbol=bot.symbol.name)
    response = Decimal(response["price"])
    return response


@with_binance_client
def binance_set_leverage(bot, client):
    client.futures_change_leverage(symbol=bot.symbol.name, leverage=bot.isLeverage)


@with_binance_client
def binance_change_position_mode_on_hedge(bot, client):
    response = client.futures_change_position_mode(symbol=bot.symbol.name, dualsideposition=True)
    return response


@with_binance_client
def binance_account_balance(bot, client):
    response = client.futures_account_balance()
    response = [x for x in response if x['asset'] == 'USDT'][0]
    response = {
        'fullBalance': round(float(response['balance']), 2),
        'availableBalance': round(float(response['availableBalance']), 2),
    }
    return response
