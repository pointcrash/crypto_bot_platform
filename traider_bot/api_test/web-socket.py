import time
from single_bot.logic.global_variables import global_list_twm_for_binance

from binance import ThreadedWebsocketManager

api_key = '40804baa38ed8e089157f32bee8c2311b0745b611b1dfb65ddfeda95af7f3b6b'
api_secret = 'cd843d65f675cc9b3619871733f8d1c8b26a63a729ddcaabf4caba1fe973bbec'

main_api_key = 'DtQ4NHexgkjnoNLKFeEiPjeFsN5vJr8UsUBigfelxO4DAyykSBZAyLRteiktUjJj'
main_api_secret = '6G3BhdLPDywx5y7QsxrYOFj3glD4bMglpifUOfjwo1gfE7KMfoadVkJCyXwac3b2'


def main():
    symbol = 'BTCUSDT'
    symbo1 = 'ETHUSDT'

    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret, testnet=True)
    # twm = ThreadedWebsocketManager(api_key=main_api_key, api_secret=main_api_secret, testnet=False)
    # global_list_twm_for_binance['my_account'] = twm

    # start is required to initialise its internal loop
    twm.start()

    def handle_socket_message(msg):
        print(msg)

    def handle_socket_messag1e(msg):
        print(msg['e'])

    def handle_socket_message_markPrise(msg):
        print(msg['data']['p'])

    # def handle_socket_message_user_info(msg):
    #     if msg['e'] == 'ORDER_TRADE_UPDATE':
    #         print(msg['e'], msg['o']['s'], msg['o']['S'], msg['o']['ps'])

    # twm.start_kline_socket(callback=handle_socket_message, symbol=symbol)
    # twm.start_futures_user_socket(callback=handle_socket_message)
    twm.start_margin_socket(callback=handle_socket_message)
    # twm.start_coin_futures_socket(callback=handle_socket_message)
    # twm.start_futures_user_socket(callback=handle_socket_messag1e)
    # print('ok')
    # twm.start_symbol_mark_price_socket(callback=handle_socket_message, symbol=symbol, fast=True)
    # twm.start_symbol_mark_price_socket(callback=handle_socket_message_markPrise, symbol=symbol, fast=True)
    # twm.start_symbol_mark_price_socket(callback=handle_socket_message, symbol=symbo1, fast=False)
    # twm.start_kline_socket(callback=handle_socket_message, symbol=symbol, interval='15m')

    # multiple sockets can be started
    # twm.start_depth_socket(callback=handle_socket_message, symbol=symbol)

    # or a multiplex socket can be started like this
    # see Binance docs for stream names
    # streams = ['bnbbtc@miniTicker', 'bnbbtc@bookTicker']
    # twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)
    # twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret, testnet=True)
    # twm.start()
    # twm.start_symbol_mark_price_socket(callback=handle_socket_message, symbol=symbol, fast=True)
    time.sleep(1000)
    twm.stop()
    twm.join()

#
# def subscribe_f():
#     symbol = 'BTCUSDT'
#
#     def handle_socket_message_markPrise(msg):
#         print(msg['data']['p'])
#     twm = global_list_twm_for_binance['my_account']
#     twm.start()
#     twm.start_symbol_mark_price_socket(callback=handle_socket_message_markPrise, symbol=symbol, fast=True)
#     twm.join()


if __name__ == "__main__":
    main()
