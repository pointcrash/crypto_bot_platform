import json
import traceback
import uuid
from decimal import Decimal

from api.api_v5_bybit import HTTP_Request
from bots.bot_logic import custom_logging


def sort_position_inform(unsorted_list):
    sorted_list = sorted(unsorted_list, key=lambda x: x['side'])
    return sorted_list


def bybit_get_position_inform(bot):
    def format_data(position_list):
        position_inform_list = [{
            'symbol': position['symbol'],
            'qty': position['size'],
            'entryPrice': position['avgPrice'],
            'markPrice': position['markPrice'],
            'unrealisedPnl': position['unrealisedPnl'],
            'side': 'LONG' if position['side'] == 'Buy' else 'SHORT',
        } for position in position_list]
        return sort_position_inform(position_inform_list)

    endpoint = "/v5/position/list"
    method = "GET"
    params = f"category=linear&symbol={bot.symbol.name}"
    response = json.loads(HTTP_Request(bot.account, endpoint, method, params))
    try:
        response = response['result']['list']
        position_inform_list = format_data(response)
        return position_inform_list
    except Exception as e:
        print(e)
        print(response)
        raise Exception(traceback.print_exc())


def bybit_place_order(bot, side, order_type, price=None, qty=None, position_side=None):
    if not position_side:
        positionIdx = 1 if side.upper() == 'BUY' else 2
    else:
        positionIdx = 1 if position_side.upper() == 'LONG' else 2

    endpoint = "/v5/order/create"
    method = "POST"
    orderLinkId = uuid.uuid4().hex
    params = {
        'category': 'linear',
        'symbol': bot.symbol.name,
        'side': side.capitalize(),
        'positionIdx': positionIdx,
        'orderType': order_type.capitalize(),
        'qty': str(qty),
        'price': str(price),
        'orderLinkId': orderLinkId,
    }

    params = json.dumps(params)
    response = json.loads(HTTP_Request(bot.account, endpoint, method, params))
    if response['result']:
        return response['result']
    else:
        custom_logging(bot, params)
        custom_logging(bot, response)
        return response


def bybit_place_conditional_order(bot, side, position_side, trigger_price, trigger_direction, qty):
    positionIdx = 1 if position_side.upper() == 'LONG' else 2

    endpoint = "/v5/order/create"
    method = "POST"
    orderLinkId = uuid.uuid4().hex
    params = {
        'category': 'linear',
        'symbol': bot.symbol.name,
        'side': side.capitalize(),
        'positionIdx': positionIdx,
        'orderType': 'MARKET',
        'qty': str(qty),
        'triggerPrice': str(trigger_price),
        'triggerDirection': str(trigger_direction),
        'orderLinkId': orderLinkId,
    }

    params = json.dumps(params)
    response = json.loads(HTTP_Request(bot.account, endpoint, method, params))
    if response['result']:
        return response['result']
    else:
        custom_logging(bot, response)


def bybit_cancel_all_orders(bot):
    endpoint = "/v5/order/cancel-all"
    method = "POST"
    params = {
        'category': bot.category,
        'symbol': bot.symbol.name,
    }
    params = json.dumps(params)
    response = json.loads(HTTP_Request(bot.account, endpoint, method, params))
    return response


def bybit_cancel_order(bot, order_id):
    endpoint = "/v5/order/cancel"
    method = "POST"
    params = {
        'category': bot.category,
        'symbol': bot.symbol.name,
        'orderId': order_id,
    }
    params = json.dumps(params)
    response = json.loads(HTTP_Request(bot.account, endpoint, method, params))
    return response


def bybit_get_open_orders(bot):
    endpoint = "/v5/order/realtime"
    method = "GET"
    params = f"category=linear&symbol={bot.symbol.name}"
    response = json.loads(HTTP_Request(bot.account, endpoint, method, params))
    try:
        response = response['result']['list']
    except Exception as e:
        print(e)
        print(response)


def bybit_get_current_price(bot, category='linear'):
    endpoint = "/v5/market/tickers"
    method = "GET"
    params = f"category={category}&symbol={bot.symbol.name}"
    response = json.loads(HTTP_Request(bot.account, endpoint, method, params))
    return Decimal(response["result"]["list"][0]["lastPrice"])


def bybit_set_leverage(bot, category='linear'):
    endpoint = "/v5/position/set-leverage"
    method = "POST"
    params = {
        'category': category,
        'symbol': bot.symbol.name,
        'buyLeverage': str(bot.isLeverage),
        'sellLeverage': str(bot.isLeverage),
    }
    params = json.dumps(params)
    response = json.loads(HTTP_Request(bot.account, endpoint, method, params, bot))
    return response


def bybit_change_position_mode_on_hedge(bot, category='linear'):
    endpoint = "/v5/position/switch-mode"
    method = "POST"
    mode = 3  # Hedge
    params = {
        'category': category,
        'symbol': bot.symbol.name,
        'mode': mode,
    }
    params = json.dumps(params)
    response = json.loads(HTTP_Request(bot.account, endpoint, method, params))
    return response


def bybit_account_balance(account):
    endpoint = "/v5/asset/transfer/query-account-coins-balance"
    method = "GET"
    params = f"accountType={account.account_type}&coin=USDT"
    response = json.loads(HTTP_Request(account, endpoint, method, params))
    response = response['result']['balance'][0]
    response = {
        'fullBalance': round(float(response['walletBalance']), 2),
        'availableBalance': round(float(response['transferBalance']), 2),
    }
    return response


def get_instruments_info(account, category, symbol=None):
    endpoint = "/v5/market/instruments-info"
    method = "GET"
    if symbol is not None:
        params = f"category={category}&symbol={symbol.name}"
    else:
        params = f"category={category}"
    response = json.loads(HTTP_Request(account, endpoint, method, params))
    return response


def get_bybit_exchange_information(account):
    data_set = get_instruments_info(account, category="linear")
    symbol_set = {
        i['symbol']: {
            'priceScale': i['priceScale'],
            'minLeverage': i['leverageFilter']['minLeverage'],
            'maxLeverage': i['leverageFilter']['maxLeverage'],
            'leverageStep': i['leverageFilter']['leverageStep'],
            'minPrice': i['priceFilter']['minPrice'],
            'maxPrice': i['priceFilter']['maxPrice'],
            'priceTickSize': i['priceFilter']['tickSize'],
            'minQty': i['lotSizeFilter']['minOrderQty'],
            'maxQty': i['lotSizeFilter']['maxOrderQty'],
            'stepQtySize': i['lotSizeFilter']['qtyStep']
        } for i in data_set['result']['list'] if i['symbol'].endswith('USDT')
    }

    return symbol_set
