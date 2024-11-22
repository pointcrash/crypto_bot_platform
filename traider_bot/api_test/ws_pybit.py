from pybit.unified_trading import WebSocket
from time import sleep

ws = WebSocket(
    trace_logging=False,
    testnet=True,
    channel_type="private",
    api_key="Rwt3UiqjKvIXe39h1W",
    api_secret="kyzgLKPSWlYzQUbJtX51tWkyiuYW3IQHXgO3",
)


def handle_message(message):
    print(message)


if __name__ == "__main__":
    ws.wallet_stream(callback=handle_message)
    while True:
        sleep(1)
