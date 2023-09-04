# from pybit.unified_trading import WebSocket
# from time import sleep
#
# ws = WebSocket(
#     testnet=False,
#     channel_type="linear",
# )
#
#
# def handle_message(message):
#     print(message['data']['b'])
#     if int(message['data']['b'][0][1]) > 1000:
#         print('-----------------')
#
#
# ws.orderbook_stream(
#     depth=1,
#     symbol="SUIUSDT",
#     callback=handle_message
# )
# while True:
#     sleep(1)
