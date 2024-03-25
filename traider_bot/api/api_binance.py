from datetime import datetime, timedelta
from decimal import Decimal

import requests
from binance.client import Client

api_key = '40804baa38ed8e089157f32bee8c2311b0745b611b1dfb65ddfeda95af7f3b6b'
api_secret = 'cd843d65f675cc9b3619871733f8d1c8b26a63a729ddcaabf4caba1fe973bbec'

client = Client(api_key, api_secret, testnet=True)


def get_data_ago_to_ms(days):
    current_date = datetime.now()
    date_ago = current_date - timedelta(days=days)
    return int(date_ago.timestamp() * 1000)


# Получение информации о балансе
# print(len(client.futures_klines(symbol='BTCUSDT', interval='15m', limit=50)))  # Получение свечей
# print(client.futures_mark_price(symbol='BTCUSDT'))  # Получаем данные по цене
# print(client.futures_symbol_ticker(symbol='BTCUSDT'))  # Получаем ТОЛЬКО price данные по цене??
# print(client.futures_comission_rate(symbol='BTCUSDT'))  # {'symbol': 'BTCUSDT', 'makerCommissionRate': '0.000200', 'takerCommissionRate': '0.000400'}
# print(client.futures_leverage_bracket())  # СПРОСИТЬ У ЮРЫ!!!
# print(client.futures_place_batch_order(batchOrders=[order1, order2]))  # Разместить несколько ордеров (max 5)
# print(client.futures_create_order(symbol='BTCUSDT', side='BUY', positionSide='LONG', type='MARKET', quantity=0.02))  # Разместить ордер
# print(client.futures_create_order(symbol='BTCUSDT', side='BUY', positionSide='SHORT', type='LIMIT', price=41000, timeInForce='GTC', quantity=0.02))  # Разместить ордер
# print(client.futures_get_all_orders(symbol='BTCUSDT'))  # Список ордеров
# print(client.futures_get_order(symbol='BTCUSDT', orderId='3653110189'))  # Инфо по открытому ордеру
# print(client.futures_cancel_order(symbol='BTCUSDT', orderId='3653110189'))  # Отменить ордер
# print(client.futures_cancel_all_open_orders(symbol='BTCUSDT'))
# print(client.futures_account_balance())  # Получить баланс кошелька
# print(client.futures_change_leverage(symbol='BTCUSDT', leverage=9))  # Изменить плечо
# print(client.futures_get_position_mode(symbol='BTCUSDT'))  # Инфо по One-way/Hedge режиму
# print(client.futures_change_position_mode(symbol='BTCUSDT', dualsideposition=True))  # Изменить режим на Hedge
# print(client.futures_position_information(symbol='BTCUSDT'))  # Инфо по позиции
# print(client.futures_klines(symbol='BTCUSDT', interval='5m', limit=20)[::-1])
# print(client.futures_income_history(symbol='BTCUSDT', incomeType='REALIZED_PNL', startTime=get_data_ago_to_ms(30)))
# x = client.futures_account_trades(symbol='BTCUSDT')
# for y in x:
#     print(y)

# print(client.futures_income_history(symbol='BTCUSDT', incomeType='FUNDING_FEE'))
# print(client.futures_create_order(symbol='BTCUSDT', side='SELL', positionSide='SHORT', type='STOP_MARKET', quantity=0.02, workingType='MARK_PRICE', stopPrice=Decimal(63000)))  # Разместить ордер

# print(client.futures_get_order(symbol='BTCUSDT'))  #
def get_exchange_information():
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


def format_kline_interval_to_binance(interval):
    if interval == '1':
        interval = '1m'
    elif interval == '3':
        interval = '3m'
    elif interval == '5':
        interval = '5m'
    elif interval == '15':
        interval = '15m'
    elif interval == '30':
        interval = '30m'
    elif interval == '60':
        interval = '1h'
    elif interval == '120':
        interval = '2h'
    elif interval == '240':
        interval = '4h'
    elif interval == '360':
        interval = '6h'
    elif interval == '720':
        interval = '8h'
    elif interval == 'D':
        interval = '1d'
    else:
        interval = None

    return interval
