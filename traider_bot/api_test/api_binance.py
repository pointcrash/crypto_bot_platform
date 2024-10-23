from datetime import datetime, timedelta
from decimal import Decimal

import requests
from binance.client import Client

from api_2.formattres import order_formatters

api_key = '40804baa38ed8e089157f32bee8c2311b0745b611b1dfb65ddfeda95af7f3b6b'
api_secret = 'cd843d65f675cc9b3619871733f8d1c8b26a63a729ddcaabf4caba1fe973bbec'
main_api_key = 'DtQ4NHexgkjnoNLKFeEiPjeFsN5vJr8UsUBigfelxO4DAyykSBZAyLRteiktUjJj'
main_api_secret = '6G3BhdLPDywx5y7QsxrYOFj3glD4bMglpifUOfjwo1gfE7KMfoadVkJCyXwac3b2'


def get_data_ago_to_ms(days):
    current_date = datetime.now()
    date_ago = current_date - timedelta(days=days)
    return int(date_ago.timestamp() * 1000)


if __name__ == '__main__':
    client = Client(api_key, api_secret, testnet=True)
    # main_client = Client(main_api_key, main_api_secret, testnet=False)

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
    # print(client.futures_get_open_orders(symbol='BTCUSDT'))  # Список ордеров
    # print(client.futures_get_order(symbol='BTCUSDT', orderId='3653110189'))  # Инфо по открытому ордеру
    # print(client.futures_cancel_order(symbol='BTCUSDT', orderId='3653110189'))  # Отменить ордер
    # print(client.futures_cancel_all_open_orders(symbol='BTCUSDT'))
    # print(client.futures_exchange_info())  # Получить баланс кошелька
    # print(client.futures_change_leverage(symbol='BTCUSDT', leverage=9))  # Изменить плечо
    # print(client.futures_get_position_mode(symbol='BTCUSDT'))  # Инфо по One-way/Hedge режиму
    # print(client.futures_change_position_mode(symbol='BTCUSDT', dualsideposition=True))  # Изменить режим на Hedge
    # for balance in client.futures_account_balance():
    #     print(balance)

    # x = (client.futures_income_history())  # Инфо по позиции
    # for i in x:
    #     print(i)

    # print(main_client.futures_change_margin_type(symbol='BTCUSDT', marginType='ISOLATED'))  # Инфо по позиции

    # response = (main_client.futures_position_information())  # Инфо по позиции
    # for i in response:
    #     if float(i['positionAmt']) != 0:
    #         print(i)
    # print(client.futures_klines(symbol='BTCUSDT', interval='5m', limit=20)[::-1])
    # print(main_client.futures_income_history(symbol='NOTUSDT', incomeType='REALIZED_PNL', startTime=get_data_ago_to_ms(30)))
    # x = main_client.futures_account_trades(symbol='NOTUSDT', startTime=get_data_ago_to_ms(23), endTime=get_data_ago_to_ms(16))
    # for y in x:
    #     print(y)

    # print(client.futures_income_history(symbol='BTCUSDT', incomeType='FUNDING_FEE'))
    # print(client.futures_create_order(symbol='BTCUSDT', side='BUY', positionSide='SHORT', type='TAKE_PROFIT_MARKET', quantity='0.02', stopPrice=Decimal(60000)))  # Разместить ордер

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
    interval_values = ['1', '3', '5', '15', '30', '60', '120', '240', '360', '720', 'D']
    transformed_values = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '1d']

    if interval in interval_values:
        index = interval_values.index(interval)
        return transformed_values[index]
    else:
        return None
