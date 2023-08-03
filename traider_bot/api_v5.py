import json
from decimal import Decimal
import requests
import time
import hashlib
import hmac

from requests import RequestException

httpClient = requests.Session()
recv_window = str(5000)


def HTTP_Request(account, endPoint, method, payload, Info=' '):
    global time_stamp
    time_stamp = str(int(time.time() * 10 ** 3))
    signature = genSignature(account.SECRET_KEY, account.API_TOKEN, payload)
    headers = {
        'X-BAPI-API-KEY': account.API_TOKEN,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': time_stamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }
    try:
        if method == "POST":
            response = requests.post(account.url + endPoint, headers=headers, data=payload)
        else:
            response = requests.get(account.url + endPoint + "?" + payload, headers=headers)
        response.raise_for_status()  # Проверка наличия ошибки в ответе
        return response.text
    except RequestException as e:
        # Обработка ошибки при отправке запроса или получении ответа
        print("An error occurred during the request:", e)
        return None
    except Exception as e:
        # Обработка других неожиданных ошибок
        print("An unexpected error occurred:", e)
        return None


def genSignature(secret_key, api_key, payload):
    param_str = str(time_stamp) + api_key + recv_window + payload
    hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
    signature = hash.hexdigest()
    return signature


def cancel_all(account, category, symbol):
    endpoint = "/v5/order/cancel-all"
    method = "POST"
    params = {
        'category': category,
        'symbol': symbol.name,
    }
    params = json.dumps(params)
    response = json.loads(HTTP_Request(account, endpoint, method, params, "CancelAll"))
    return response


def get_current_price(account, category, symbol):
    endpoint = "/v5/market/tickers"
    method = "GET"
    params = f"category={category}&symbol={symbol.name}"
    response = json.loads(HTTP_Request(account, endpoint, method, params, "Price"))
    return Decimal(response["result"]["list"][0]["lastPrice"])


def get_position_price(symbol_list):
    if len(symbol_list) == 1:
        return Decimal(symbol_list[0]["avgPrice"])
    else:
        return [Decimal(i['avgPrice']) for i in symbol_list]


def get_qty(symbol_list):
    if len(symbol_list) == 1:
        return Decimal(symbol_list[0]["size"])
    else:
        return [Decimal(qty['size']) for qty in symbol_list]


def get_side(symbol_list):
    if len(symbol_list) == 1:
        return symbol_list[0]["side"]
    else:
        return [i['side'] for i in symbol_list]


def get_list(account, category, symbol):
    try:
        endpoint = "/v5/position/list"
        method = "GET"
        params = f"category={category}&symbol={symbol.name}"
        response = json.loads(HTTP_Request(account, endpoint, method, params, "Price"))
        return response['result']['list']
    except Exception as e:
        print(e)


def get_order_book(account, category, symbol):
    endpoint = "/v5/market/orderbook"
    method = "GET"
    params = f"category={category}&symbol={symbol.name}"
    response = json.loads(HTTP_Request(account, endpoint, method, params, "Price"))
    # print(response)
    return None


def get_instruments_info(account, category, symbol=None):
    endpoint = "/v5/market/instruments-info"
    method = "GET"
    if symbol is not None:
        params = f"category={category}&symbol={symbol.name}"
    else:
        params = f"category={category}"
    response = json.loads(HTTP_Request(account, endpoint, method, params))
    return response


def get_symbol_set():
    from main.models import Account

    account_data = {
        "name": "John Doe",
        "API_TOKEN": "35cvb1aYDNlbIe7bZd",
        "SECRET_KEY": "1X9PNigz5mRcPwknuOZeeKSkDa0dDR6v14a4",
        "is_mainnet": False,
        "url": "https://api-testnet.bybit.com"
    }

    account = Account(
        name=account_data["name"],
        API_TOKEN=account_data["API_TOKEN"],
        SECRET_KEY=account_data["SECRET_KEY"],
        is_mainnet=account_data["is_mainnet"],
        url=account_data["url"]
    )

    data_set = get_instruments_info(account, category="linear")
    symbol_set = [(i['symbol'], i['priceScale'], i['leverageFilter']['minLeverage'], i['leverageFilter']['maxLeverage'],
                   i['leverageFilter']['leverageStep'], i['priceFilter']['minPrice'], i['priceFilter']['maxPrice'],
                   i['lotSizeFilter']['minOrderQty'], i['lotSizeFilter']['maxOrderQty']) for i in data_set['result']['list'] if
                  i['symbol'].endswith('USDT')]

    return symbol_set


def get_order_status(account, category, symbol, orderLinkId):
    endpoint = "/v5/order/realtime"
    method = "GET"
    params = f"category={category}&symbol={symbol}&orderLinkId={orderLinkId}"
    response = json.loads(HTTP_Request(account, endpoint, method, params))
    try:
        return response['result']['list'][0]['orderStatus']
    except:
        return "Order does not exist"


def get_pnl(account, category, symbol, start_time=0):
    endpoint = "/v5/position/closed-pnl"
    method = "GET"
    params = f"category={category}&symbol={symbol}&startTime={start_time}"
    response = json.loads(HTTP_Request(account, endpoint, method, params))
    try:
        return response['result']['list']
    except Exception as e:
        print(e, response)


def set_leverage(account, category, symbol, leverage):
    endpoint = "/v5/position/set-leverage"
    method = "POST"
    params = {
        'category': category,
        'symbol': symbol.name,
        'buyLeverage': str(leverage),
        'sellLeverage': str(leverage),
    }
    params = json.dumps(params)
    response = json.loads(HTTP_Request(account, endpoint, method, params))


def get_balance(account):
    endpoint = "/v5/account/wallet-balance"
    method = "GET"
    params = f"accountType=CONTRACT"
    response = json.loads(HTTP_Request(account, endpoint, method, params))
    return response


def get_query_account_coins_balance(account):
    endpoint = "/v5/asset/transfer/query-account-coins-balance"
    method = "GET"
    params = f"accountType=CONTRACT&coin=USDT"
    response = json.loads(HTTP_Request(account, endpoint, method, params))
    try:
        return response['result']['balance']
    except:
        return None


def switch_position_mode(bot):
    endpoint = "/v5/position/switch-mode"
    method = "POST"
    mode = 0
    if bot.category == 'inverse':
        mode = 3

    params = {
        'category': bot.category,
        'symbol': bot.symbol.name,
        'mode': mode,
    }
    params = json.dumps(params)
    response = json.loads(HTTP_Request(bot.account, endpoint, method, params))
