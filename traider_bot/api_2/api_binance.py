from decimal import Decimal
from functools import wraps
from binance.client import Client

from api_2.custom_logging_api import custom_logging


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

    custom_logging(bot, f'binance_get_position_inform(symbol={bot.symbol.name})', 'REQUEST')
    response = client.futures_position_information(symbol=bot.symbol.name)
    custom_logging(bot, response, 'RESPONSE')
    position_inform_list = format_data(response)
    return position_inform_list


@with_binance_client
def binance_place_order(bot, client, side, order_type, price, qty, position_side, timeInForce='GTC'):
    if order_type.capitalize() == 'Market':
        price = None
    if not position_side:
        position_side = 'LONG' if side.upper() == 'BUY' else 'SHORT'

    params = {
        'symbol': bot.symbol.name,
        'side': side.upper(),
        'positionSide': position_side,
        'type': order_type.upper(),
        'price': price,
        'timeInForce': timeInForce,
        'quantity': qty,
    }

    custom_logging(bot, f'binance_place_order({params})', 'REQUEST')
    response = client.futures_create_order(
        symbol=bot.symbol.name,
        side=side.upper(),
        positionSide=position_side,
        type=order_type.upper(),
        price=price,
        timeInForce=timeInForce,
        quantity=qty,
    )
    custom_logging(bot, response, 'RESPONSE')
    return response


@with_binance_client
def binance_place_conditional_order(bot, client, side, position_side, trigger_price, trigger_direction, qty):
    if trigger_direction == 1:
        if side == 'SELL' and (position_side == 'LONG' or position_side == 'SHORT'):
            order_type = 'TAKE_PROFIT_MARKET'
        else:
            order_type = 'STOP_MARKET'
    else:
        if side == 'BUY' and (position_side == 'LONG' or position_side == 'SHORT'):
            order_type = 'TAKE_PROFIT_MARKET'
        else:
            order_type = 'STOP_MARKET'

    if not position_side:
        position_side = 'LONG' if side.upper() == 'BUY' else 'SHORT'

    params = {
        'symbol': bot.symbol.name,
        'side': side,
        'positionSide': position_side,
        'type': order_type,
        'stopPrice': trigger_price,
        'quantity': qty,
    }

    custom_logging(bot, f'binance_place_conditional_order({params})', 'REQUEST')

    response = client.futures_create_order(
        symbol=bot.symbol.name,
        side=side,
        positionSide=position_side,
        type=order_type,
        stopPrice=trigger_price,
        quantity=qty,
    )
    custom_logging(bot, response, 'RESPONSE')
    return response


@with_binance_client
def binance_place_batch_order(bot, client, order_list):
    for order in order_list:
        if not order.get('timeInForce') and order.get('type') == 'LIMIT':
            order['timeInForce'] = 'GTC'
        order['quantity'] = order.pop('qty')

    custom_logging(bot, f'binance_place_batch_order({order_list})', 'REQUEST')
    response = client.futures_place_batch_order(batchOrders=order_list)
    custom_logging(bot, response, 'RESPONSE')
    return response


@with_binance_client
def binance_cancel_all_orders(bot, client):
    custom_logging(bot, f'binance_cancel_all_orders({bot.symbol.name})', 'REQUEST')
    response = client.futures_cancel_all_open_orders(symbol=bot.symbol.name)
    custom_logging(bot, response, 'RESPONSE')
    return response


@with_binance_client
def binance_cancel_order(bot, client, order_id):
    custom_logging(bot, f'binance_cancel_order({bot.symbol.name}, orderId={order_id})', 'REQUEST')
    response = client.futures_cancel_order(symbol=bot.symbol.name, orderId=order_id)
    custom_logging(bot, response, 'RESPONSE')
    return response


@with_binance_client
def binance_get_open_orders(bot, client):
    custom_logging(bot, f'binance_get_open_orders({bot.symbol.name})', 'REQUEST')
    response = client.futures_get_open_orders(symbol=bot.symbol.name)
    custom_logging(bot, response, 'RESPONSE')
    return response


@with_binance_client
def binance_get_current_price(bot, client):
    custom_logging(bot, f'binance_get_current_price({bot.symbol.name})', 'REQUEST')
    response = client.futures_symbol_ticker(symbol=bot.symbol.name)
    custom_logging(bot, response, 'RESPONSE')
    price = Decimal(response["price"])
    return price


@with_binance_client
def binance_set_leverage(bot, client):
    custom_logging(bot, f'binance_set_leverage({bot.symbol.name} leverage={bot.leverage})', 'REQUEST')
    response = client.futures_change_leverage(symbol=bot.symbol.name, leverage=bot.leverage)
    custom_logging(bot, response, 'RESPONSE')


@with_binance_client
def binance_change_position_mode_on_hedge(bot, client):
    custom_logging(bot, f'binance_change_position_mode_on_hedge({bot.symbol.name})', 'REQUEST')
    response = client.futures_change_position_mode(symbol=bot.symbol.name, dualsideposition=True)
    custom_logging(bot, response, 'RESPONSE')
    return response


def binance_account_balance(account):
    client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=not account.is_mainnet)
    response = client.futures_account_balance()
    response = [x for x in response if x['asset'] == 'USDT'][0]
    response = {
        'fullBalance': round(float(response['balance']), 2),
        'availableBalance': round(float(response['availableBalance']), 2),
    }
    return response


def get_binance_exchange_information(account):
    client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=not account.is_mainnet)

    def count_decimal_places(number_str):
        if '.' in number_str:
            decimal_value = number_str.split(".")[1]
            zero_count = decimal_value.split("1")[0]
            return len(zero_count) + 1
        else:
            return 0

    symbols_raw_data = client.futures_exchange_info()
    symbol_set = {
        i['symbol']: {
            'minPrice': i['filters'][0]['minPrice'],
            'maxPrice': i['filters'][0]['maxPrice'],
            'priceTickSize': i['filters'][0]['tickSize'],
            'priceScale': count_decimal_places(i['filters'][0]['tickSize']),
            'minQty': i['filters'][2]['minQty'],
            'maxQty': i['filters'][2]['maxQty'],
            'stepQtySize': i['filters'][2]['stepSize']
        } for i in symbols_raw_data['symbols'] if i['symbol'].endswith('USDT')
    }

    leverage_raw_data = client.futures_leverage_bracket()
    for obj in leverage_raw_data:
        if obj['symbol'] in symbol_set:
            symbol_set[obj['symbol']]['maxLeverage'] = obj['brackets'][0]['initialLeverage']

    return symbol_set
