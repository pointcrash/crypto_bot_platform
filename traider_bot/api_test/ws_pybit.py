from pybit.unified_trading import WebSocket
from time import sleep

ws = WebSocket(
    trace_logging=True,
    testnet=False,
    channel_type="private",
    api_key="xcXVA47NndHFNDBqJ9",
    api_secret="71Xj99PBSljGv8wOer2iRnBt7xF2J6UsF7Ex",
)


def handle_message(message):
    print(message)


if __name__ == "__main__":
    ws.position_stream(callback=handle_message)
    while True:
        sleep(1)
