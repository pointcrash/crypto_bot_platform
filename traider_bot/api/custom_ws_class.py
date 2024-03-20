import asyncio
import json
import threading
import time

import websockets


class CustomWebSocketClient:
    def __init__(self, callback, account_name, service_name):
        self.uri = "ws://ws-manager:8765"
        self.callback = callback
        self.account_name = account_name
        self.service = service_name
        self.websocket = None

    def is_open(self):
        status = self.websocket.open
        return status

    async def connect(self):
        self.websocket = await websockets.connect(self.uri)
        await self.websocket.send(json.dumps({'title': 'conn', 'account': self.account_name}))

    async def send_sub_to_mark_price(self, **kwargs):
        await self.websocket.send(json.dumps({'title': 'sub',
                                              'topic': 'mark_price',
                                              'service': self.service,
                                              'symbol': kwargs['symbol'],
                                              }))

    async def send_sub_to_kline(self, **kwargs):
        await self.websocket.send(json.dumps({'title': 'sub',
                                              'topic': 'kline',
                                              'service': self.service,
                                              'symbol': kwargs['symbol'],
                                              'interval': kwargs['interval'],
                                              }))

    async def receive_messages(self):
        try:
            while self.websocket.open:
            # async for message in self.websocket:
                message = await self.websocket.recv()
                message = json.loads(message)
                # print(message)
                self.callback(message)
        finally:
            if self.websocket.open:
                await self.websocket.close()

    async def websocket_close(self):
        await self.websocket.close()

    async def run(self):
        await self.connect()
        await self.receive_messages()

    @staticmethod
    def run_event_loop(function, **kwargs):
        asyncio.run(function(**kwargs))

    def start_async_function_in_threads(self, function, **kwargs):
        thread = threading.Thread(target=self.run_event_loop, args=(function,), kwargs=kwargs)
        thread.start()
        return thread

    def start(self):
        self.start_async_function_in_threads(self.run)

    def close(self):
        thread = self.start_async_function_in_threads(self.websocket_close)
        thread.join()

    def sub_to_mark_price(self, symbol):
        self.start_async_function_in_threads(self.send_sub_to_mark_price, symbol=symbol)

    def sub_to_kline(self, symbol: str, interval: str):
        self.start_async_function_in_threads(self.send_sub_to_kline, symbol=symbol, interval=interval)


def message_callback(message):
    print(f"Received message: {message}")


if __name__ == "__main__":
    account_name = 'My Bibnance Account'
    client = CustomWebSocketClient(message_callback, account_name, service_name='Binance')
    client.start()
    print('end')
    c = 0
    while True:
        print('app working...')
        time.sleep(3)
        if c == 0:
            client.sub_to_mark_price('BTCUSDT')
            client.sub_to_kline('BTCUSDT', '1')
            c += 1
