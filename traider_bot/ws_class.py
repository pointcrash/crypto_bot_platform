# import hmac
# import json
# import threading
# import time
# import websocket
#
# from bots.bot_logic import logging
#
# AVAILABLE_CHANNEL_TYPES = [
#     "inverse",
#     "linear",
#     "spot",
#     "option",
#     "private",
# ]
#
#
# class BybitWebSocketClient:
#     def __init__(self, callback_func=None, class_obj=None, channel_type='private', is_mainnet=False, api_key='', api_secret=''):
#         self.api_key = api_key
#         self.api_secret = api_secret
#         self.is_mainnet = is_mainnet
#         self.channel_type = channel_type
#         self.urls_choices = {
#             'mainnet': f'wss://stream.bybit.com/v5/{channel_type}',
#             'testnet': f'wss://stream-testnet.bybit.com/v5/{channel_type}'
#         }
#         self.callback = callback_func
#         self.class_obj = class_obj
#         self.ws = None
#         self.wst = None
#         self.manual_closing = False
#
#         self.connect()
#
#     def on_message(self, ws, message):
#         data = json.loads(message)
#         if not self.class_obj or not self.callback:
#             print(data)
#         else:
#             topic = data.get('topic', '')
#             if '.' in topic:
#                 topic = topic.split('.')[0]
#             self.callback(self.class_obj, topic, data)
#
#     def on_error(self, ws, error):
#         print(f'WS on_error func: {error}')
#
#     def on_close(self, ws, close_status, close_msg):
#         print("### Connection closed ###", close_status, close_msg)
#         if not self.manual_closing:
#             print("### Reconnecting in 1 sec ###")
#             time.sleep(1)
#             self.connect()
#
#     def send_auth(self, ws):
#         expires = int((time.time() + 10) * 1000)
#         _val = f'GET/realtime{expires}'
#         signature = str(hmac.new(
#             bytes(self.api_secret, 'utf-8'),
#             bytes(_val, 'utf-8'), digestmod='sha256'
#         ).hexdigest())
#         ws.send(json.dumps({"op": "auth", "args": [self.api_key, expires, signature]}))
#
#     def on_open(self, ws):
#         print('opened')
#         if self.api_key and self.api_secret:
#             self.send_auth(ws)
#
#     def subscribe(self, topic, symbol=''):
#         print('send subscription ' + topic + ' ' + symbol)
#         if symbol:
#             topic += '.' + symbol
#         self.ws.send(json.dumps({"op": "subscribe", "args": [topic]}))
#
#     def run_forever_in_thread(self):
#         self.wst = threading.Thread(
#             target=lambda: self.ws.run_forever(
#                 ping_interval=20,
#                 ping_timeout=10,
#             )
#         )
#         self.wst.start()
#
#     def connect(self):
#         conn_url = self.urls_choices['mainnet' if self.is_mainnet else 'testnet']
#         if self.channel_type == 'public':
#             conn_url += '/linear'
#         self.ws = websocket.WebSocketApp(
#             conn_url,
#             on_message=self.on_message,
#             on_error=self.on_error,
#             on_close=self.on_close,
#             on_open=self.on_open
#         )
#         self.manual_closing = False
#         self.run_forever_in_thread()
#
#     def is_connected(self):
#         try:
#             if self.ws.sock.connected:
#                 return True
#             else:
#                 return False
#         except AttributeError:
#             return False
#
#     def close(self):
#         if self.ws:
#             self.manual_closing = True
#             self.ws.close()
#             print('ws connection closed')
#
#
