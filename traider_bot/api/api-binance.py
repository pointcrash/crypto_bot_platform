from binance.client import Client


api_key = '40804baa38ed8e089157f32bee8c2311b0745b611b1dfb65ddfeda95af7f3b6b'
api_secret = 'cd843d65f675cc9b3619871733f8d1c8b26a63a729ddcaabf4caba1fe973bbec'

client = Client(api_key, api_secret, testnet=True)

# Получение информации о балансе
# print(len(client.futures_klines(symbol='BTCUSDT', interval='15m', limit=50)))  # Получение свечей
# print(client.futures_mark_price(symbol='BTCUSDT'))  # Получаем данные по цене
# print(client.futures_symbol_ticker(symbol='BTCUSDT'))  # Получаем ТОЛЬКО price данные по цене??
# print(client.futures_comission_rate(symbol='BTCUSDT'))  # {'symbol': 'BTCUSDT', 'makerCommissionRate': '0.000200', 'takerCommissionRate': '0.000400'}
# print(client.futures_leverage_bracket(symbol='BTCUSDT'))  # СПРОСИТЬ У ЮРЫ!!!
# print(client.futures_create_order(symbol='BTCUSDT', side='BUY', type='MARKET', quantity=0.02))  # Разместить ордер
# print(client.futures_create_order(symbol='BTCUSDT', side='BUY', type='LIMIT', price=41000, timeInForce='GTC', quantity=0.02))  # Разместить ордер
# print(client.futures_get_all_orders(symbol='BTCUSDT'))  # Список ордеров
# print(client.futures_get_order(symbol='BTCUSDT', orderId='3653110189'))  # Инфо по открытому ордеру
# print(client.futures_cancel_order(symbol='BTCUSDT', orderId='3653110189'))  # Отменить ордер
# print(client.futures_cancel_all_open_orders(symbol='BTCUSDT'))  # Отменит все ордера
# print(client.futures_account_balance())  # Получить баланс кошелька
# print(client.futures_change_leverage(symbol='BTCUSDT', leverage=9))  # Изменить плечо
# print(client.futures_get_position_mode(symbol='BTCUSDT'))  # Инфо по One-way/Hedge режиму
# print(client.futures_change_position_mode(symbol='BTCUSDT', dualsideposition=True))  # Изменить режим на Hedge
# print(client.futures_position_information(symbol='BTCUSDT'))  # Инфо по позиции


# print(client.futures_get_order(symbol='BTCUSDT'))  #
def get_exchange_information():
    data_set = client.futures_exchange_info()
    symbol_set = {
        i['symbol']: {
            'minPrice': i['filters'][0]['minPrice'],
            'maxPrice': i['filters'][0]['maxPrice'],
            'priceTickSize': i['filters'][0]['tickSize'],
            'minQty': i['filters'][2]['minQty'],
            'maxQty': i['filters'][2]['maxQty'],
            'stepQtySize': i['filters'][2]['stepSize']
        } for i in data_set['symbols'] if i['symbol'].endswith('USDT')
    }
    return symbol_set

