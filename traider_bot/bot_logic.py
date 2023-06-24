import json
import statistics
from decimal import Decimal

from api_v5 import HTTP_Request


class BollingerBands:
    def __init__(self, category, symbol, interval, qty_cline, d):
        self.category = category
        self.symbol = symbol
        self.interval = interval
        self.qty_cline = qty_cline
        self.d = d

    def get_kline(self):
        endpoint = "/v5/market/kline"
        method = "GET"
        params = f"category={self.category}&symbol={self.symbol}&interval={self.interval}&limit={self.qty_cline}"
        response = json.loads(HTTP_Request(endpoint, method, params, "Cline"))
        return response["result"]["list"]

    def get_closePrice_list(self):
        closePrice_list = []
        for i in self.get_kline():
            closePrice_list.append(Decimal(i[4]))
        return closePrice_list

    def calculation_ML(self):
        return sum(self.get_closePrice_list()) / len(self.get_closePrice_list())

    def calculation_std_dev(self):
        return statistics.stdev(self.get_closePrice_list())

    def calculation_TL(self):
        return self.calculation_ML() + (self.d * self.calculation_std_dev())

    def calculation_BL(self):
        return self.calculation_ML() - (self.d * self.calculation_std_dev())
