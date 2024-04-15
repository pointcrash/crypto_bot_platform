from pybit.unified_trading import WebSocket
from time import sleep


# ws = WebSocket(
#     testnet=True,
#     channel_type="linear",
# )


def handle_message(message):
    print(message)
#
#
# def handle_position_stream_message(message):
#     for psn in message['data']:
#         if psn['symbol'] == 'SANDUSDT':
#             print(psn['positionIdx'], '-', psn['size'])
#     print(message)


ws_private = WebSocket(
    # trace_logging=True,
    testnet=True,
    channel_type="private",
    api_key="XlXhlUPG4GCBGRdFld",
    api_secret="JBpwCjzkzXbxriLdptaoLyLR2wvdNSz0NisU",
)

#
# ws_private2 = WebSocket(
#     trace_logging=True,
#     testnet=True,
#     channel_type="private",
#     api_key="bxuxnvO1jyS7eMMDif",
#     api_secret="UHRa0V8yc2UxYNTutzn6az8b4QqGnP94Addm",
# )

# ws_private.ticker_stream(symbol="BTCUSDT", callback=handle_message)
ws_private.position_stream(callback=handle_message)

count = 0

while count < 111:
    count += 1
    # print('ws_public', ws.is_connected())
    print('ws_private', ws_private.is_connected())
    sleep(1)
    if count == 100:
        # ws.exit()
        ws_private.exit()
        # ws_private2.exit()
