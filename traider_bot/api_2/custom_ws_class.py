import json
import logging
import os
import threading
import time
import traceback

import websocket

from api_2.custom_logging_api import custom_logging
from bots.general_functions import custom_user_bot_logging, update_bots_conn_status, update_bots_is_active, \
    update_bots_forcibly_stopped
from django.core.cache import cache

bot_logger = logging.getLogger('bot_logger')


class CustomWSClient:
    def __init__(self, callback=None, bot=None):
        self.url = "ws://ws-manager:8765"
        self.bot = bot
        self.bot_id = bot.id
        self.symbol = bot.symbol.name
        self.callback = callback
        self.logger = get_logger_for_bot_ws_msg(bot.id)
        self.account_name = bot.account.name
        self.service = bot.account.service.name
        self.ping_interval = 20
        self.ping_timeout = 10
        self.max_retries = 5  # Максимальное количество попыток переподключения
        self.retry_delay = 10  # Задержка перед переподключением (в секундах)
        self.retry_count = 0
        self.stop_reconnect = False
        self.wst = None
        self.ws = None
        self.sub_list = []

    def _initialize_ws(self):
        self.ws = websocket.WebSocketApp(
            url=self.url,
            on_message=self._on_message,
            on_close=self._on_close,
            on_open=self._on_open,
            on_error=self._on_error,
            on_pong=self._on_pong,
        )

    def start(self):
        self.stop_reconnect = False
        self.retry_count = 0  # Сброс попыток при запуске
        self._connect()

    def _connect(self):
        self._initialize_ws()
        self.wst = threading.Thread(
            target=lambda: self.ws.run_forever(),
            name=f'CustomWSClient_Thread_BotID_{self.bot.id}'
        )
        self.wst.daemon = True
        self.wst.start()
        bot_logger.info(f'Bot {self.bot.pk} socket started')
        update_bots_conn_status(self.bot, new_status=True)

    def _on_message(self, ws, message):
        try:
            if self.bot.restart_try is True:
                self.bot.restart_try = False
                self.bot.save(update_fields=['restart_try'])

            cache.set(f'ws-{self.bot.id}-q-{os.getenv("CELERY_QUEUE_NAME")}', True, timeout=5)

            if cache.get(f'close_ws_{self.bot_id}'):
                bot_logger.info(f'Bot {self.bot.pk} got signal to close')
                cache.delete(f'close_ws_{self.bot_id}')
                self.bot.is_active = False
                self.exit()
                return

            message = json.loads(message)
            if message['symbol'] == self.symbol:
                # self.logger.debug(message)
                bot_logger.debug(f'BOT-{self.bot_id}, message: {message}')
                self.callback(message)
        except Exception as e:
            custom_logging(self.bot, f'GET ERROR IN "_on_message" func: {e}')
            custom_logging(self.bot, f"**Traceback:** {traceback.format_exc()}")
            custom_logging(self.bot, f"**СООБЩЕНИЕ ВЫЗВАШЕЕ ОШИБКУ:** {message}")

    def _on_close(self, ws, close_code, reason):
        update_bots_conn_status(self.bot, new_status=False)

        close_code = close_code or 'Unknown'
        reason = reason or 'No reason provided'

        custom_logging(self.bot, f'WebSocket closed. Close code: {close_code}, Reason: {reason}')
        custom_user_bot_logging(self.bot, f'WebSocket closed. Close code: {close_code}, Reason: {reason}')
        bot_logger.info(f'Bot {self.bot.pk} connection closed. Close code: {close_code}, Reason: {reason}')

        self._attempt_reconnect()

    def _on_open(self, ws):
        update_bots_conn_status(self.bot, new_status=True)
        custom_logging(self.bot, f'WebSocket connection open.')
        bot_logger.info(f'Bot {self.bot.pk} connection opened')
        self.retry_count = 0

        bot_logger.debug(f'sub_list {self.sub_list}')
        if self.sub_list:
            for sub_method in self.sub_list:
                sub_method()
            self.sub_list = []

    def _on_error(self, ws, error):
        custom_logging(self.bot, f'Error: {error}')
        bot_logger.error(f'Bot {self.bot.pk} get error {error}', exc_info=False)

    def _attempt_reconnect(self):
        if self.stop_reconnect:
            bot_logger.info(f'Bot {self.bot.pk} not tried reconnect because used manual stop')
            return
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            bot_logger.info(f'Attempting to reconnect Bot {self.bot.pk}, attempt {self.retry_count}/{self.max_retries}')
            time.sleep(self.retry_delay)
            self._connect()
        else:
            bot_logger.error(f'Maximum retry attempts reached for Bot {self.bot.pk}. Giving up.')
            update_bots_is_active(self.bot, new_status=False)
            update_bots_forcibly_stopped(self.bot, forcibly_stopped=True)

    def _on_pong(self, ws):
        pass

    def sub_to_user_info(self):
        self.logger.debug('Message from sub_to_user_info')

        if self.sub_to_user_info not in self.sub_list:
            self.sub_list.append(self.sub_to_user_info)

        self.ws.send(json.dumps({'title': 'conn', 'account': self.account_name}))

    def sub_to_kline(self, interval=None):
        self.logger.debug('Message from sub_to_kline')
        if not interval:
            interval = self.bot.bb.interval

        if self.sub_to_kline not in self.sub_list:
            self.sub_list.append(self.sub_to_kline)

        subscribe_message = {'title': 'sub', 'topic': 'kline', 'service': self.service, 'symbol': self.bot.symbol.name,
                             'interval': interval}
        self.ws.send(json.dumps(subscribe_message))

    def sub_to_mark_price(self):
        self.logger.debug('Message from sub_to_mark_price')

        if self.sub_to_mark_price not in self.sub_list:
            self.sub_list.append(self.sub_to_mark_price)

        subscribe_message = {'title': 'sub', 'topic': 'mark_price', 'service': self.service,
                             'symbol': self.bot.symbol.name}
        self.ws.send(json.dumps(subscribe_message))

    def is_connected(self):
        try:
            if self.ws.sock and self.ws.sock.connected:
                return True
            else:
                return False
        except AttributeError:
            return False

    def exit(self):
        self.stop_reconnect = True
        bot_logger.info(f'Bot {self.bot.pk} initiate "exit" method for ws')
        self.ws.close()


def get_logger_for_bot_ws_msg(bot_id):
    formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s')

    logger = logging.getLogger(f'BOT_{bot_id}')
    logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler(f'logs/bots/ws_data/bot_{bot_id}.log')
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger
