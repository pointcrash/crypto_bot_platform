import asyncio
import json

import websockets
from binance import AsyncClient, BinanceSocketManager

api_key = '40804baa38ed8e089157f32bee8c2311b0745b611b1dfb65ddfeda95af7f3b6b'
api_secret = 'cd843d65f675cc9b3619871733f8d1c8b26a63a729ddcaabf4caba1fe973bbec'
queue = asyncio.Queue()
active_connections = []


async def binance_client():
    # uri = "ws://localhost:8765"  # Адрес WebSocket сервера
    client = await AsyncClient.create(api_key=api_key, api_secret=api_secret, testnet=True)
    bm = BinanceSocketManager(client)
    ts = bm.symbol_mark_price_socket(symbol='BTCUSDT', fast=True)
    async with ts as tscm:
        # async with websockets.connect(uri) as websocket:
        while True:
            message = await tscm.recv()
            # print(message)
            await queue.put(message)
            # print(res_msg)
            # await websocket.send(json.dumps(res_msg))


async def websocket_server(websocket, path):
    print("Client connected")
    active_connections.append(websocket)
    try:
        async for message in websocket:
            print('recv message', message)
    except websockets.exceptions.ConnectionClosedError:
        active_connections.remove(websocket)
        print("Client disconnected")


async def send_data_to_clients():
    print("Send data task started")
    while True:
        data = await queue.get()
        print("Sending data:", data['data']['P'])
        for websocket in active_connections:
            await websocket.send(json.dumps(data['data']['P']))


async def start_server():
    server = await websockets.serve(websocket_server, "localhost", 8765)
    await server.wait_closed()


async def main():
    task1 = asyncio.create_task(start_server())
    send_data_task = asyncio.create_task(send_data_to_clients())
    await asyncio.gather(task1, send_data_task, binance_client())


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(binance_client())
