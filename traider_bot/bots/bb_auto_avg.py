from api_v5 import get_current_price
from decimal import Decimal

from orders.models import Order


def get_USDT_from_qty(qty, price):
    return qty * price


class BBAutoAverage:
    def __init__(self, bot, psn_price, psn_side, psn_qty, bb_obj):
        self.bot = bot
        self.account = bot.account
        self.category = bot.category
        self.symbol = bot.symbol
        self.avg_percent = bot.bb_avg_percent
        self.dfm = bot.dfm
        self.chw = bot.chw
        self.max_margin = bot.max_margin
        self.psn_price = psn_price
        self.psn_side = psn_side
        self.psn_qty = psn_qty
        self.bb_obj = bb_obj

    def auto_avg(self):
        current_price = get_current_price(self.account, self.category, self.symbol)
        if self.psn_side == 'Buy' and self.bb_obj.ml <= self.psn_price:
            if self.channel_width_check(current_price):
                if self.dfm_check(current_price, self.bb_obj.bl):
                    if self.margin_limit_check(current_price):
                        self.to_average()
                        return True
            return False

        elif self.psn_side == 'Sell' and self.bb_obj.ml >= self.psn_price:
            if self.channel_width_check(current_price):
                if self.dfm_check(current_price, self.bb_obj.tl):
                    if self.margin_limit_check(current_price):
                        self.to_average()
                        return True
            return False

    def channel_width_check(self, current_price):
        if self.bb_obj.tl - self.bb_obj.bl >= current_price * Decimal(self.chw) / 100:
            return True
        else:
            return False

    def dfm_check(self, current_price, bb):
        if abs(current_price - self.bb_obj.ml) >= abs(bb - self.bb_obj.ml) * Decimal(self.dfm) / 100:
            return True
        else:
            return False

    def margin_limit_check(self, current_price):
        qty_avg = self.psn_qty * self.avg_percent / 100
        USDT_value_before_avg = get_USDT_from_qty(self.psn_qty, self.psn_price)
        USDT_value_avg = get_USDT_from_qty(qty_avg, current_price)
        USDT_value = USDT_value_avg + USDT_value_before_avg

        if USDT_value < self.max_margin:
            return True
        else:
            return False

    def to_average(self):
        avg_order = Order.objects.create(
            bot=self.bot,
            category=self.category,
            symbol=self.symbol.name,
            side=self.psn_side,
            orderType="Market",
            qty=self.psn_qty * self.avg_percent / 100
        )
