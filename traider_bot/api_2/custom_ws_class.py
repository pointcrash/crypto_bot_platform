import json
import logging
import threading
import traceback

import websocket

from api_2.custom_logging_api import custom_logging


class CustomWSClient:
    def __init__(self, callback=None, bot=None):
        self.url = "ws://ws-manager:8765"
        self.bot = bot
        self.symbol = bot.symbol.name
        self.callback = callback
        self.logger = get_logger_for_bot_ws_msg(bot.id)
        self.account_name = bot.account.name
        self.service = bot.account.service.name
        self.ping_interval = 20
        self.ping_timeout = 10
        self.wst = None
        self.ws = websocket.WebSocketApp(
            url=self.url,
            on_message=self._on_message,
            on_close=self._on_close,
            on_open=self._on_open,
            on_error=self._on_error,
            on_pong=self._on_pong,
        )

    def start(self):
        self.wst = threading.Thread(
            target=lambda: self.ws.run_forever(), name=f'CustomWSClient_Thread_BotID_{self.bot.id}')

        # Configure as daemon; start.
        self.wst.daemon = True
        self.wst.start()

    def _on_message(self, ws, message):
        try:
            message = json.loads(message)
            if message['symbol'] == self.symbol:
                self.logger.debug(message)
                self.callback(message)
        except Exception as e:
            custom_logging(self.bot, f'GET ERROR IN "_on_message" func: {e}')
            custom_logging(self.bot, f"**Traceback:** {traceback.format_exc()}")

    def _on_close(self, ws, close_code, reason):
        pass

    def _on_open(self, ws):
        print('BotID', self.bot.id, "Connection opened")

    def _on_error(self, ws, error):
        print('BotID', self.bot.id, f"Error: {error}")

    def _on_pong(self, ws):
        pass

    def sub_to_user_info(self):
        self.ws.send(json.dumps({'title': 'conn', 'account': self.account_name}))

    def sub_to_kline(self, interval):
        subscribe_message = {'title': 'sub', 'topic': 'kline', 'service': self.service, 'symbol': self.bot.symbol.name,
                             'interval': interval}
        self.ws.send(json.dumps(subscribe_message))

    def sub_to_mark_price(self):
        subscribe_message = {'title': 'sub', 'topic': 'mark_price', 'service': self.service,
                             'symbol': self.bot.symbol.name}
        self.ws.send(json.dumps(subscribe_message))

    def is_connected(self):
        try:
            if self.ws.sock.connected:
                return True
            else:
                return False
        except AttributeError:
            return False

    def exit(self):
        self.ws.close()
        self.wst.join()
        while self.ws.sock:
            continue
        print('BotID', self.bot.id, "WebSocket connection closed.")


def get_logger_for_bot_ws_msg(bot_id):
    formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s')

    logger = logging.getLogger(f'BOT_{bot_id}')
    logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler(f'logs/bot_{bot_id}.log')
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger
