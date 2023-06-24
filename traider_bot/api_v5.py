import json
import math
import uuid
from decimal import Decimal, ROUND_DOWN

import requests
from config import *
import time
import hashlib
import hmac

api_key = API_KEY
secret_key = API_SECRET
httpClient = requests.Session()
recv_window = str(5000)
url = "https://api-testnet.bybit.com"  # Testnet endpoint
entry_qty = 0.006
total_qty = 0


def HTTP_Request(endPoint, method, payload, Info=' '):
    global time_stamp
    time_stamp = str(int(time.time() * 10 ** 3))
    signature = genSignature(payload)
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': time_stamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }
    if (method == "POST"):
        response = httpClient.request(method, url + endPoint, headers=headers, data=payload)
    else:
        response = httpClient.request(method, url + endPoint + "?" + payload, headers=headers)
    # print(response.text)
    # print(Info + " Elapsed Time : " + str(response.elapsed))
    return response.text


def genSignature(payload):
    param_str = str(time_stamp) + api_key + recv_window + payload
    hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
    signature = hash.hexdigest()
    return signature


def orders():
    global total_qty
    endpoint = "/v5/order/create"
    method = "POST"
    orderLinkId = uuid.uuid4().hex
    total_qty += entry_qty
    print(total_qty)

    params = {
        'category': 'linear',
        'symbol': 'BTCUSDT',
        'side': 'Sell',
        'positionIdx': 0,
        'orderType': 'Market',
        'qty': str(entry_qty),
        'timeInForce': 'GTC',
        'orderLinkId': orderLinkId
    }
    params = json.dumps(params)
    HTTP_Request(endpoint, method, params, "Create")


def create_take_1():
    endpoint = "/v5/order/create"
    method = "POST"
    orderLinkId = uuid.uuid4().hex
    qty = round(get_qty_BTC() / 2, 3)
    price = get_position_price_BTC()
    price_sell = round(price * Decimal('1.01'), 2)

    params = {
        'category': 'linear',
        'symbol': 'BTCUSDT',
        'side': 'Sell',
        'positionIdx': 0,
        'orderType': 'Limit',
        'qty': str(qty),
        'price': str(price_sell),
        'timeInForce': 'GTC',
        'orderLinkId': orderLinkId
    }
    params = json.dumps(params)
    HTTP_Request(endpoint, method, params, "Create")


def create_take_2():
    global total_qty
    endpoint = "/v5/order/create"
    method = "POST"
    orderLinkId = uuid.uuid4().hex
    qty = round(total_qty / 2, 3)
    print(qty)
    price = get_position_price_BTC()
    price_sell = price * Decimal('1.02')
    price_sell = round(price_sell, 2)
    print(price_sell)

    params = {
        'category': 'linear',
        'symbol': 'BTCUSDT',
        'side': 'Sell',
        'positionIdx': 0,
        'orderType': 'Limit',
        'qty': str(qty),
        'price': str(price_sell),
        'timeInForce': 'GTC',
        'orderLinkId': orderLinkId
    }
    params = json.dumps(params)
    HTTP_Request(endpoint, method, params, "Create")


def cancel_all(category, symbol):
    endpoint = "/v5/order/cancel-all"
    method = "POST"
    params = {
        'category': category,
        'symbol': symbol,
    }
    params = json.dumps(params)
    HTTP_Request(endpoint, method, params, "CancelAll")


def get_current_price(category, symbol):
    endpoint = "/v5/market/tickers"
    method = "GET"
    params = f"category={category}&symbol={symbol}"
    response = json.loads(HTTP_Request(endpoint, method, params, "Price"))
    # print('BTC price = ', response["result"]["list"][0]["lastPrice"])
    return Decimal(response["result"]["list"][0]["lastPrice"])


def get_position_price(symbol_list):
    return Decimal(symbol_list["avgPrice"])


def get_qty(symbol_list):
    return Decimal(symbol_list["size"])


def get_positional_side(symbol_list):
    return symbol_list["side"]


def get_list(category, symbol):
    endpoint = "/v5/position/list"
    method = "GET"
    params = f"category={category}&symbol={symbol}"
    response = json.loads(HTTP_Request(endpoint, method, params, "Price"))
    # print(response["result"]["list"][0])
    return response["result"]["list"][0]


# def transfer_to_USDT():

# print(get_qty_BTC(get_BTC_list()))
# print(math.floor((0.001/2) * 1000) / 1000)
# print("Buy" if "Bsdf" == "Sell" else "Sell")
