# from pybit.unified_trading import WebSocket
# from time import sleep
#
# '''
#                 #MyMainKey
#         api_key = "Apz7mrOcJzFhbFrHLo"
#     api_secret = "qzJyJ9cTEzRB1aSPO9h6PHBvy9B2C4udTGSL"
#
#         #MyTestNetKey - risk96testnet
#         api_key = "bxuxnvO1jyS7eMMDif"
#     api_secret = "UHRa0V8yc2UxYNTutzn6az8b4QqGnP94Addm"
# '''
# #
# # ws = WebSocket(
# #     testnet=True,
# #     channel_type="linear",
# # )
#
#
# def handle_message(message):
#     print(len(message['data']))
#     print(message)
#
#
# def handle_position_stream_message(message):
#     for psn in message['data']:
#         if psn['symbol'] == 'SANDUSDT':
#             print(psn['positionIdx'], '-', psn['size'])
#     print(message)
#
#
# ws_private = WebSocket(
#     trace_logging=True,
#     testnet=True,
#     channel_type="private",
#     api_key="bxuxnvO1jyS7eMMDif",
#     api_secret="UHRa0V8yc2UxYNTutzn6az8b4QqGnP94Addm",
# )
#
# ws_private2 = WebSocket(
#     trace_logging=True,
#     testnet=True,
#     channel_type="private",
#     api_key="bxuxnvO1jyS7eMMDif",
#     api_secret="UHRa0V8yc2UxYNTutzn6az8b4QqGnP94Addm",
# )
# #
# # ws.ticker_stream(
# #     symbol="SANDUSDT",
# #     callback=handle_message
# # )
#
# # ws_private.execution_stream(callback=handle_message)
# # ws_private.order_stream(callback=handle_message)
#
# # ws_private.position_stream(callback=handle_position_stream_message)
#
# while True:
#     print('ws_private', ws_private.is_connected())
#     print('ws_private-2', ws_private2.is_connected())
#     sleep(1)
