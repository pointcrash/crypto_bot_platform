from datetime import datetime, timedelta

import pytz

from api_v5 import get_current_price
from decimal import Decimal, ROUND_DOWN

from bots.models import Log
from orders.models import Order
from timezone.models import TimeZone


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
        self.dfep = bot.dfep
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
                    if self.margin_limit_check():
                        if self.dfep_check(current_price):
                            self.to_average(current_price)
                            return True
            return False

        elif self.psn_side == 'Sell' and self.bb_obj.ml >= self.psn_price:
            if self.channel_width_check(current_price):
                if self.dfm_check(current_price, self.bb_obj.tl):
                    if self.margin_limit_check():
                        if self.dfep_check(current_price):
                            self.to_average(current_price)
                            return True
            return False

    def channel_width_check(self, current_price):
        if self.bb_obj.tl - self.bb_obj.bl >= current_price * Decimal(self.chw) / 100:
            return True
        else:
            return False

    def dfm_check(self, current_price, bb):
        if self.psn_side == 'Buy':
            if current_price < self.bb_obj.ml:
                if abs(current_price - self.bb_obj.ml) >= abs(bb - self.bb_obj.ml) * Decimal(self.dfm) / 100:
                    return True
        else:
            if current_price > self.bb_obj.ml:
                if abs(current_price - self.bb_obj.ml) >= abs(bb - self.bb_obj.ml) * Decimal(self.dfm) / 100:
                    return True

    def margin_limit_check(self):
        if not self.max_margin:
            return True
        else:
            psn_currency_amount = self.psn_price * self.psn_qty / self.bot.isLeverage
            avg_currency_amount = psn_currency_amount * self.bot.bb_avg_percent / 100

            if psn_currency_amount + avg_currency_amount > self.max_margin:
                logging(self.bot,
                        f'MARGIN LIMIT! Max margin -> {self.bot.max_margin}, Margin after avg -> {psn_currency_amount + avg_currency_amount}')
                return False
            else:
                return True

    def dfep_check(self, current_price):
        if not self.dfep:
            return True
        elif abs(current_price - self.psn_price) >= ((self.psn_price / 100) * self.dfep):
            return True
        else:
            return False

    def to_average(self, current_price):
        psn_currency_amount = self.psn_price * self.psn_qty / self.bot.isLeverage
        avg_currency_amount = Decimal(psn_currency_amount * self.bot.bb_avg_percent / 100)
        qty = get_quantity_from_price(avg_currency_amount, current_price, self.bot.symbol.minOrderQty,
                                      self.bot.isLeverage)

        avg_order = Order.objects.create(
            bot=self.bot,
            category=self.category,
            symbol=self.symbol.name,
            side=self.psn_side,
            orderType="Market",
            qty=qty
        )
        logging(self.bot, 'Усредняющий ордер резмещен')


def get_quantity_from_price(qty_USDT, price, minOrderQty, leverage):
    return (Decimal(str(qty_USDT * leverage)) / price).quantize(Decimal(minOrderQty), rounding=ROUND_DOWN)


def logging(bot, text):
    user = bot.owner
    timezone = TimeZone.objects.filter(users=user).first()
    gmt0 = pytz.timezone('GMT')
    date = datetime.now(gmt0).replace(microsecond=0)
    bot_info = f'Bot {bot.pk} {bot.symbol.name} {bot.side} {bot.interval}'
    gmt = 0

    if timezone:
        gmt = int(timezone.gmtOffset)
        if gmt > 0:
            date = date + timedelta(seconds=gmt)
        else:
            date = date - timedelta(seconds=gmt)

    if gmt > 0:
        str_gmt = '+' + str(gmt / 3600)
    elif gmt < 0:
        str_gmt = str(gmt / 3600)
    else:
        str_gmt = str(gmt)

    in_time = f'{date.time()} {date.date()}'
    Log.objects.create(bot=bot, content=f'{bot_info} {text} {in_time} (GMT {str_gmt})')
