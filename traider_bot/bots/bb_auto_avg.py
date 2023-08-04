from api_v5 import get_current_price
from decimal import Decimal, ROUND_DOWN

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
        print(current_price)
        print(self.bb_obj.ml, self.psn_price)
        if self.psn_side == 'Buy' and self.bb_obj.ml <= self.psn_price:
            if self.channel_width_check(current_price):
                if self.dfm_check(current_price, self.bb_obj.bl):
                    if self.margin_limit_check():
                        self.to_average(current_price)
                        return True
            return False

        elif self.psn_side == 'Sell' and self.bb_obj.ml >= self.psn_price:
            if self.channel_width_check(current_price):
                if self.dfm_check(current_price, self.bb_obj.tl):
                    if self.margin_limit_check():
                        self.to_average(current_price)
                        return True
            return False

    def channel_width_check(self, current_price):
        print(self.bb_obj.tl - self.bb_obj.bl)
        print(current_price * Decimal(self.chw) / 100)
        if self.bb_obj.tl - self.bb_obj.bl >= current_price * Decimal(self.chw) / 100:
            return True
        else:
            return False

    def dfm_check(self, current_price, bb):
        print(abs(current_price - self.bb_obj.ml))
        print(abs(bb - self.bb_obj.ml) * Decimal(self.dfm) / 100)
        if abs(current_price - self.bb_obj.ml) >= abs(bb - self.bb_obj.ml) * Decimal(self.dfm) / 100:
            return True
        else:
            return False

    def margin_limit_check(self):
        psn_currency_amount = self.psn_price * self.psn_qty
        avg_currency_amount = psn_currency_amount * self.bot.bb_avg_percent / 100

        if psn_currency_amount + avg_currency_amount > self.max_margin:
            return False
        else:
            return True

    def to_average(self, current_price):
        psn_currency_amount = self.psn_price * self.psn_qty
        avg_currency_amount = Decimal(psn_currency_amount * self.bot.bb_avg_percent / 100)
        qty = get_quantity_from_price(avg_currency_amount, current_price, self.bot.minOrderQty)

        avg_order = Order.objects.create(
            bot=self.bot,
            category=self.category,
            symbol=self.symbol.name,
            side=self.psn_side,
            orderType="Market",
            qty=qty
        )


def get_quantity_from_price(qty_USDT, price, minOrderQty):
    return (Decimal(str(qty_USDT)) / price).quantize(Decimal(minOrderQty), rounding=ROUND_DOWN)
