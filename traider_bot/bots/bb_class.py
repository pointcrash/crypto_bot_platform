import json
import statistics
import time
from decimal import Decimal
from datetime import datetime, timedelta
from binance.client import Client
from api.api_binance import format_kline_interval_to_binance

from api.api_v5_bybit import HTTP_Request


class BollingerBands:
    def __init__(self, bot):
        self.account = bot.account
        self.category = bot.category
        self.symbol = bot.symbol.name
        self.priceScale = int(bot.symbol.priceScale)
        self.interval = bot.interval
        self.qty_kline = bot.qty_kline
        self.d = bot.d
        self.close_price_list = self.get_new_close_price_list
        self.ml = self.get_ml
        self.std_dev = self.get_std_dev
        self.tl = self.get_tl
        self.bl = self.get_bl
        self.kline_list = [[time.time() - 90000]]  # получаем значение времени на 25 часов раньше текущего

    # def istime_update_kline(self):
    #     if datetime.now() - datetime.fromtimestamp(float(self.kline_list[0][0]) / 1000.0) > timedelta(
    #             minutes=int(self.interval)):
    #         return True
    #     return False

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
            # if not self.istime_update_kline():
            #     return self.kline_list
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
        print(self.close_price_list, len(self.close_price_list))

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



# l = [[1710000900000, '68214.10', '68259.50', '68193.90', '68245.00', '135.193', 1710001199999, '9224745.78500', 3219, '88.270', '6023290.07730', '0'], [1710000600000, '68217.70', '68245.00', '68209.00', '68214.00', '173.542', 1710000899999, '11839737.38220', 3746, '103.797', '7081508.49670', '0'], [1710000300000, '68241.10', '68246.80', '68189.90', '68217.60', '351.782', 1710000599999, '23997766.46050', 7539, '167.250', '11409532.39820', '0'], [1710000000000, '68341.50', '68373.90', '68241.10', '68241.20', '314.464', 1710000299999, '21481389.97540', 6320, '140.314', '9586205.45940', '0'], [1709999700000, '68321.40', '68343.40', '68281.30', '68341.60', '206.240', 1709999999999, '14089514.14900', 4494, '99.070', '6767978.07300', '0'], [1709999400000, '68347.00', '68362.90', '68321.40', '68321.40', '109.867', 1709999699999, '7508137.24190', 3229, '39.307', '2686254.36680', '0'], [1709999100000, '68370.80', '68376.00', '68292.40', '68347.00', '282.471', 1709999399999, '19301328.29330', 5208, '95.241', '6507757.69080', '0'], [1709998800000, '68355.80', '68411.00', '68355.80', '68370.90', '260.782', 1709999099999, '17835126.57010', 4886, '157.080', '10742884.39030', '0'], [1709998500000, '68374.90', '68384.30', '68343.90', '68355.80', '165.220', 1709998799999, '11294971.12090', 3327, '70.239', '4801781.65260', '0'], [1709998200000, '68336.70', '68398.40', '68336.60', '68374.90', '368.088', 1709998499999, '25166640.05110', 5932, '180.159', '12317351.10680', '0'], [1709997900000, '68272.10', '68338.50', '68272.10', '68336.40', '207.578', 1709998199999, '14178602.45650', 3520, '140.382', '9588946.53620', '0'], [1709997600000, '68283.30', '68313.20', '68268.30', '68272.00', '147.753', 1709997899999, '10090196.91790', 3291, '64.992', '4438509.55380', '0'], [1709997300000, '68222.50', '68316.20', '68222.40', '68283.30', '358.480', 1709997599999, '24479062.10790', 6239, '251.109', '17147508.38700', '0'], [1709997000000, '68239.90', '68240.00', '68217.20', '68222.40', '191.915', 1709997299999, '13094579.29580', 4754, '96.770', '6602522.35980', '0'], [1709996700000, '68215.20', '68261.60', '68204.70', '68239.90', '225.210', 1709996999999, '15365776.09310', 5455, '129.040', '8804342.87080', '0'], [1709996400000, '68189.00', '68271.10', '68188.90', '68215.20', '741.864', 1709996699999, '50618710.94500', 9222, '376.653', '25699463.05610', '0'], [1709996100000, '68174.10', '68217.50', '68155.90', '68189.00', '441.719', 1709996399999, '30121595.35910', 6726, '276.011', '18821902.36690', '0'], [1709995800000, '68205.90', '68228.00', '68125.40', '68174.10', '867.408', 1709996099999, '59125498.91680', 12404, '331.517', '22597918.12110', '0'], [1709995500000, '68278.90', '68323.00', '68166.00', '68205.90', '1906.109', 1709995799999, '130062489.63710', 21986, '568.465', '38786947.82010', '0'], [1709995200000, '68368.10', '68382.00', '68259.40', '68279.00', '1003.695', 1709995499999, '68557040.27570', 9406, '272.081', '18582754.79410', '0'], [1709994900000, '68342.80', '68407.60', '68328.90', '68368.10', '347.258', 1709995199999, '23743005.60900', 5010, '139.327', '9526913.98280', '0']]
# for s in l:
#     print(s)