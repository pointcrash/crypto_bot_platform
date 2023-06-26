import json
import math
import statistics
import uuid
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
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
    return Decimal(response["result"]["list"][0]["lastPrice"])


def get_position_price(symbol_list):
    return Decimal(symbol_list["avgPrice"])


def get_qty(symbol_list):
    return Decimal(symbol_list["size"])


def get_side(symbol_list):
    return symbol_list["side"]


def get_list(category, symbol):
    endpoint = "/v5/position/list"
    method = "GET"
    params = f"category={category}&symbol={symbol}"
    response = json.loads(HTTP_Request(endpoint, method, params, "Price"))
    # print(response["result"]["list"][0])
    return response["result"]["list"][0]


# print(get_qty_BTC(get_BTC_list()))
# print(math.floor((0.001/2) * 1000) / 1000)
# print("Buy" if "Bsdf" == "Sell" else "Sell")
# print(0.005 % (2 / 10**3))
