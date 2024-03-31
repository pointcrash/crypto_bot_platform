import json
import os
import uuid
from decimal import Decimal

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from binance.client import Client
from api_test.api_v5_bybit import HTTP_Request
from main.models import Account
from bots.models import BotModel

api_key_binance = '40804baa38ed8e089157f32bee8c2311b0745b611b1dfb65ddfeda95af7f3b6b'
api_secret_binance = 'cd843d65f675cc9b3619871733f8d1c8b26a63a729ddcaabf4caba1fe973bbec'

api_key_bybit = 'XlXhlUPG4GCBGRdFld'
api_secret_bybit = 'JBpwCjzkzXbxriLdptaoLyLR2wvdNSz0NisU'


def place_order(account, symbol, qty, side, order_type, timeInForce=None, price=None, ):
    if account.service.name == 'Binance':
        # positionSide = 'LONG' if side.lower() == 'buy' else 'SHORT'
        positionSide = 'SHORT' if side.lower() == 'buy' else 'LONG'
        client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)
        return client.futures_create_order(
            symbol=symbol,
            side=side.upper(),
            positionSide=positionSide,
            type=order_type.upper(),
            price=price,
            timeInForce=timeInForce,
            quantity=qty
        )

    elif account.service.name == 'ByBit':
        endpoint = "/v5/order/create"
        method = "POST"
        orderLinkId = uuid.uuid4().hex
        positionIdx = 1 if side.lower() == 'buy' else 2
        params = {
            'category': 'linear',
            'symbol': symbol,
            'side': side.capitalize(),
            'positionIdx': positionIdx,
            'orderType': order_type.capitalize(),
            'qty': str(qty),
            'price': str(price),
            'orderLinkId': orderLinkId,
        }

        params = json.dumps(params)
        response = HTTP_Request(account, endpoint, method, params)
        return response


def get_open_orders(account, symbol, category='linear'):
    if account.service.name == 'Binance':
        client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)
        return client.futures_get_open_orders(symbol=symbol)

    elif account.service.name == 'ByBit':
        endpoint = "/v5/order/realtime"
        method = "GET"
        params = f"category=linear&symbol={symbol}"
        response = json.loads(HTTP_Request(account, endpoint, method, params))
        return response['result']['list']


def cancel_all(account, symbol, category='linear'):
    if account.service.name == 'Binance':
        client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)
        response = client.futures_cancel_all_open_orders(symbol=symbol)  # Отменит все ордера

    elif account.service.name == 'ByBit' and category:
        endpoint = "/v5/order/cancel-all"
        method = "POST"
        params = {
            'category': category,
            'symbol': symbol,
        }
        params = json.dumps(params)
        response = json.loads(HTTP_Request(account, endpoint, method, params))


def cancel_order(account, symbol, order_id, category='linear'):
    if account.service.name == 'Binance':
        client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)
        response = client.futures_cancel_order(symbol=symbol, orderId=order_id)  # Отменит все ордера
        return response

    elif account.service.name == 'ByBit':
        endpoint = "/v5/order/cancel"
        method = "POST"
        params = {
            'category': category,
            'symbol': symbol,
            'orderId': order_id,
        }
        params = json.dumps(params)
        response = json.loads(HTTP_Request(account, endpoint, method, params))
        return response


def get_position_inform(account, symbol):
    def format_data(service_name, position_list):
        def sort_function(unsorted_list):
            sorted_list = sorted(unsorted_list, key=lambda x: x['side'])
            return sorted_list

        position_inform_list = []
        if service_name == 'Binance':
            position_inform_list = [{
                'symbol': position['symbol'],
                'qty': position['positionAmt'],
                'entryPrice': position['entryPrice'],
                'markPrice': position['markPrice'],
                'unrealisedPnl': position['unRealizedProfit'],
                'side': position['positionSide'],
            } for position in position_list]
        elif service_name == 'ByBit':
            position_inform_list = [{
                'symbol': position['symbol'],
                'qty': position['size'],
                'entryPrice': position['avgPrice'],
                'markPrice': position['markPrice'],
                'unrealisedPnl': position['unrealisedPnl'],
                'side': 'LONG' if position['side'] == 'Buy' else 'SHORT',
            } for position in position_list]
        return sort_function(position_inform_list)

    if account.service.name == 'Binance':
        client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)
        response = client.futures_position_information(symbol=symbol)
        position_inform_list = format_data('Binance', response)
        return position_inform_list

    elif account.service.name == 'ByBit':
        endpoint = "/v5/position/list"
        method = "GET"
        if symbol:
            params = f"category=linear&symbol={symbol}"
        else:
            params = f"category=linear&settleCoin=USDT"
        response = json.loads(HTTP_Request(account, endpoint, method, params))
        response = response['result']['list']
        position_inform_list = format_data('ByBit', response)
        return position_inform_list


def get_current_price(account, symbol, category='linear'):
    if account.service.name == 'Binance':
        client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)
        response = client.futures_symbol_ticker(symbol=symbol)
        response = Decimal(response["price"])
        return response

    elif account.service.name == 'ByBit':
        endpoint = "/v5/market/tickers"
        method = "GET"
        params = f"category={category}&symbol={symbol}"
        response = json.loads(HTTP_Request(account, endpoint, method, params))
        try:
            return Decimal(response["result"]["list"][0]["lastPrice"])
        except:
            return None


def set_leverage(account, symbol, leverage, bot=None, category='linear'):
    if account.service.name == 'Binance':
        client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)
        client.futures_change_leverage(symbol=symbol, leverage=leverage)  # Изменить плечо

    elif account.service.name == 'ByBit':
        endpoint = "/v5/position/set-leverage"
        method = "POST"
        params = {
            'category': category,
            'symbol': symbol,
            'buyLeverage': str(leverage),
            'sellLeverage': str(leverage),
        }
        params = json.dumps(params)
        json.loads(HTTP_Request(account, endpoint, method, params, bot))


def switch_position_mode(account, symbol, category='linear'):
    response = None
    if account.service.name == 'Binance':
        client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)
        response = client.futures_change_position_mode(symbol=symbol, dualsideposition=True)

    elif account.service.name == 'ByBit':
        endpoint = "/v5/position/switch-mode"
        method = "POST"
        mode = 3
        params = {
            'category': category,
            'symbol': symbol,
            'mode': mode,
        }
        params = json.dumps(params)
        response = json.loads(HTTP_Request(account, endpoint, method, params))

    return response


def get_query_account_coins_balance(account):
    if account.service.name == 'Binance':
        client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)
        response = client.futures_account_balance()
        response = [x for x in response if x['asset'] == 'USDT'][0]
        response = {
            'fullBalance': round(float(response['balance']), 2),
            'availableBalance': round(float(response['availableBalance']), 2),
        }
        return response

    elif account.service.name == 'ByBit':
        endpoint = "/v5/asset/transfer/query-account-coins-balance"
        method = "GET"
        params = f"accountType={account.account_type}&coin=USDT"
        response = json.loads(HTTP_Request(account, endpoint, method, params))
        response = response['result']['balance'][0]
        response = {
            'fullBalance': round(float(response['walletBalance']), 2),
            'availableBalance': round(float(response['transferBalance']), 2),
        }
        try:
            return response
        except:
            return None


# def get_exchange_information(account):
#     client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)
#     symbols_raw_data = client.futures_exchange_info()
#     symbol_set = {
#         i['symbol']: {
#             'minPrice': i['filters'][0]['minPrice'],
#             'maxPrice': i['filters'][0]['maxPrice'],
#             'priceTickSize': i['filters'][0]['tickSize'],
#             'minQty': i['filters'][2]['minQty'],
#             'maxQty': i['filters'][2]['maxQty'],
#             'stepQtySize': i['filters'][2]['stepSize']
#         } for i in symbols_raw_data['symbols'] if i['symbol'].endswith('USDT')
#     }
#
#     leverage_raw_data = client.futures_leverage_bracket()
#     for obj in leverage_raw_data:
#         if obj['symbol'] in symbol_set:
#             symbol_set[obj['symbol']]['maxLeverage'] = obj['brackets'][0]['initialLeverage']
#
#     return symbol_set


if __name__ == '__main__':
    account_binance = Account.objects.get(pk=6)
    account_bybit = Account.objects.get(pk=1)
    binance_bot = BotModel.objects.get(pk=529)
    bybit_bot = BotModel.objects.get(pk=530)
    # print(s.lower())
    # print(s.upper())
    # print(s.capitalize())

    # print(place_order(
    #     account=account_bybit,
    #     symbol='BTCUSDT',
    #     qty=0.02,
    #     side='Sell',
    #     order_type='Limit',
    #     price=42000,
    # ))

    print(place_order(
        account=account_binance,
        symbol='BTCUSDT',
        qty=0.02,
        side='BUY',
        order_type='MARKET',
    ))
    #
    # print(get_position_inform(
    #     account=account_bybit,
    #     symbol='BTCUSDT',
    # ))
    #
    # print(get_position_inform(
    #     account=account_binance,
    #     symbol='BTCUSDT',
    # ))
