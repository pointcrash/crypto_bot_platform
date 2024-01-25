import json
import statistics
import time
from decimal import Decimal
from datetime import datetime, timedelta

from api.api_v5_bybit import HTTP_Request


class BollingerBands:
    def __init__(self, account, category: str, symbol_name, symbol_priceScale, interval: int, qty_cline: int, d: int):
        self.account = account
        self.category = category
        self.symbol = symbol_name
        self.priceScale = int(symbol_priceScale)
        self.interval = interval
        self.qty_cline = qty_cline
        self.d = d
        self.kline_list = [[time.time() - 90000]]  # получаем значение времени на 25 часов раньше текущего

    def istime_update_kline(self):
        if datetime.now() - datetime.fromtimestamp(float(self.kline_list[0][0]) / 1000.0) > timedelta(
                minutes=int(self.interval)):
            return True
        return False

    def get_kline(self):
        if not self.istime_update_kline():
            return self.kline_list
        endpoint = "/v5/market/kline"
        method = "GET"
        params = f"category={self.category}&symbol={self.symbol}&interval={self.interval}&limit={self.qty_cline+1}"
        response = json.loads(HTTP_Request(self.account, endpoint, method, params, "Cline"))
        self.kline_list = response["result"]["list"]
        return response["result"]["list"]

    @property
    def closePrice_list(self):
        closePrice_list = []
        klines = self.get_kline()
        for i in klines[1:]:
            closePrice_list.append(Decimal(i[4]))
        return closePrice_list

    @property
    def ml(self):
        return round(Decimal(str(sum(self.closePrice_list) / self.qty_cline)), self.priceScale)

    @property
    def std_dev(self):
        return Decimal(str(statistics.stdev(self.closePrice_list)))

    @property
    def tl(self):
        return round(Decimal(str(self.ml + (self.d * self.std_dev))), self.priceScale)

    @property
    def bl(self):
        return round(Decimal(str(self.ml - (self.d * self.std_dev))), self.priceScale)
