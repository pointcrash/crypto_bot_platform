from pybit.unified_trading import WebSocket
from time import sleep

ws = WebSocket(
    trace_logging=False,
    testnet=True,
    channel_type="private",
    api_key="7rCy48L5n9daxtqRnq",
    api_secret="7CwA9GKhRcwOFCf6v5EL7Wkt1VytQsKVIKMC",
)


def handle_message(message):
    print(message)


if __name__ == "__main__":
    ws.wallet_stream(callback=handle_message)
    while True:
        sleep(1)
