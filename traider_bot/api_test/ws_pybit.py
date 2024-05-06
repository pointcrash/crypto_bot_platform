from pybit.unified_trading import WebSocket
from time import sleep

ws = WebSocket(
    testnet=False,
    channel_type="private",
    api_key="xcXVA47NndHFNDBqJ9",
    api_secret="71Xj99PBSljGv8wOer2iRnBt7xF2J6UsF7Ex",
)


def handle_message(message):
    print(message)


ws.wallet_stream(callback=handle_message)
while True:
    sleep(1)
