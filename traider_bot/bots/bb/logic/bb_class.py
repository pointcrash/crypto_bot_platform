import json
import statistics
import time
from decimal import Decimal
from binance.client import Client
from api_test.api_binance import format_kline_interval_to_binance

from api_test.api_v5_bybit import HTTP_Request


class BollingerBands:
    def __init__(self, bot):
        self.account = bot.account
        self.category = bot.category
        self.symbol = bot.symbol.name
        self.priceScale = int(bot.symbol.priceScale)
        self.interval = bot.bb.interval
        self.qty_kline = bot.bb.qty_kline
        self.d = bot.bb.d
        self.close_price_list = self.get_new_close_price_list
        self.ml = self.get_ml
        self.std_dev = self.get_std_dev
        self.tl = self.get_tl
        self.bl = self.get_bl
        self.kline_list = [[time.time() - 90000]]  # получаем значение времени на 25 часов раньше текущего

    @property
    def get_kline_list(self):
        if self.account.service.name == 'Binance':
            client = Client(self.account.API_TOKEN, self.account.SECRET_KEY, testnet=not self.account.is_mainnet)
            response = client.futures_klines(
                symbol=self.symbol,
                interval=format_kline_interval_to_binance(self.interval),
                limit=self.qty_kline + 1,
            )
            self.kline_list = response[::-1]

        elif self.account.service.name == 'ByBit':
            endpoint = "/v5/market/kline"
            method = "GET"
            params = f"category={self.category}&symbol={self.symbol}&interval={self.interval}&limit={self.qty_kline + 1}"
            response = json.loads(HTTP_Request(self.account, endpoint, method, params, "Cline"))
            self.kline_list = response["result"]["list"]
        return self.kline_list

    @property
    def get_new_close_price_list(self):
        close_price_list = []
        klines = self.get_kline_list
        for i in klines[1:]:
            close_price_list.append(Decimal(i[4]))
        return close_price_list

    def modify_close_price_list(self, new_value):
        self.close_price_list.pop()
        self.close_price_list.insert(0, new_value)

    def recalculate_lines(self):
        self.ml = self.get_ml
        self.std_dev = self.get_std_dev
        self.tl = self.get_tl
        self.bl = self.get_bl

    @property
    def get_ml(self):
        return round(Decimal(str(sum(self.close_price_list) / self.qty_kline)), self.priceScale)

    @property
    def get_std_dev(self):
        return Decimal(str(statistics.stdev(self.close_price_list)))

    @property
    def get_tl(self):
        return round(Decimal(str(self.ml + (self.d * self.std_dev))), self.priceScale)

    @property
    def get_bl(self):
        return round(Decimal(str(self.ml - (self.d * self.std_dev))), self.priceScale)
