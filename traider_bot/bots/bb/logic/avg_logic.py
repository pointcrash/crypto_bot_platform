from datetime import datetime, timedelta

import pytz

from decimal import Decimal, ROUND_DOWN
from api_2.api_aggregator import place_order

from bots.models import Log
from timezone.models import TimeZone


class BBAutoAverage:
    def __init__(self, bot, bb_obj):
        self.bot = bot
        self.account = bot.account
        self.category = bot.category
        self.symbol = bot.symbol
        self.avg_percent = bot.bb.avg_percent
        self.dfm = bot.bb.dfm
        self.chw = bot.bb.chw
        self.dfep = bot.bb.dfep
        self.max_margin = bot.bb.max_margin
        self.psn_price = None
        self.psn_side = None
        self.psn_qty = None
        self.bb_obj = bb_obj

        self.have_permission = True

    def _checking_rules(self, current_price, bb_price):
        if self._channel_width_check(current_price):
            if self._dfm_check(current_price, bb_price):
                if self._margin_limit_check():
                    if self._dfep_check(current_price):
                        return True
        return False

    def _checking_hard_avg_rules(self, current_price):
        if self.bot.bb.hard_avg_type == 'pnl':
            qty = self.psn_qty
            qty = -qty if self.psn_side == 'SHORT' else qty

            psn_cost = self.psn_price * qty
            cur_psn_cost = current_price * qty
            pnl = cur_psn_cost - psn_cost
            if pnl <= -(self.bot.amount_long * self.bot.bb.hard_avg_percent / 100):
                return True
        elif self.bot.bb.hard_avg_type == 'percent':
            change_percent = (current_price - self.psn_price) / self.psn_price * 100
            change_percent = -change_percent if self.psn_side == 'LONG' else change_percent
            if change_percent > self.bot.bb.hard_avg_percent:
                return True

    def auto_avg(self, current_price: Decimal):
        bb_price = None
        if self.bot.bb.auto_avg:
            if self.psn_side == 'LONG' and self.bb_obj.ml <= self.psn_price:
                bb_price = self.bb_obj.bl
            elif self.psn_side == 'SHORT' and self.bb_obj.ml >= self.psn_price:
                bb_price = self.bb_obj.tl

        if self.have_permission:
            if bb_price and self._checking_rules(current_price, bb_price) is True:
                self.to_average(current_price)
                self.have_permission = False
                return True

            elif self.bot.bb.hard_avg:
                if self._checking_hard_avg_rules(current_price) and self._margin_limit_check():
                    self.to_average(current_price)
                    self.have_permission = False
                    return True

        return False

    def _channel_width_check(self, current_price):
        if self.bb_obj.tl - self.bb_obj.bl >= current_price * Decimal(self.chw) / 100:
            return True
        else:
            return False

    def _dfm_check(self, current_price, bb):
        if self.psn_side == 'LONG':
            if current_price < self.bb_obj.ml:
                if abs(current_price - self.bb_obj.ml) >= abs(bb - self.bb_obj.ml) * Decimal(self.dfm) / 100:
                    return True
        elif self.psn_side == 'SHORT':
            if current_price > self.bb_obj.ml:
                if abs(current_price - self.bb_obj.ml) >= abs(bb - self.bb_obj.ml) * Decimal(self.dfm) / 100:
                    return True

    def _margin_limit_check(self):
        if not self.max_margin:
            return True
        else:
            psn_currency_amount = self.psn_price * self.psn_qty / self.bot.leverage
            avg_currency_amount = psn_currency_amount * self.avg_percent / 100

            if psn_currency_amount + avg_currency_amount > self.max_margin:
                last_log = Log.objects.filter(bot=self.bot).last()
                if 'MARGIN LIMIT!' not in last_log.content:
                    custom_logging(self.bot,
                                   f'MARGIN LIMIT! Max margin -> {self.max_margin}, Margin after avg -> {round(psn_currency_amount + avg_currency_amount, 2)}')
                return False
            else:
                return True

    def _dfep_check(self, current_price):
        if not self.dfep:
            return True
        elif abs(current_price - self.psn_price) >= ((self.psn_price / 100) * self.dfep):
            return True
        else:
            return False

    def to_average(self, current_price):
        # psn_currency_amount = self.psn_price * self.psn_qty / self.bot.leverage
        # avg_currency_amount = Decimal(psn_currency_amount * self.avg_percent / 100)
        side = 'BUY' if self.psn_side == 'LONG' else 'SELL'
        qty = Decimal(self.psn_qty) * self.avg_percent / 100

        response = place_order(self.bot, side=side, position_side=self.psn_side, order_type="MARKET", price=current_price, qty=qty)
        custom_logging(self.bot, f'Усредняющий ордер резмещен {response}')

    def update_psn_info(self, data):
        self.psn_price = Decimal(data['entryPrice'])
        self.psn_side = data['side']
        self.psn_qty = Decimal(data['qty'])
        self.have_permission = True


def get_quantity_from_price(qty_USDT, price, minOrderQty, leverage):
    return (Decimal(str(qty_USDT * leverage)) / price).quantize(Decimal(minOrderQty), rounding=ROUND_DOWN)


def custom_logging(bot, text):
    user = bot.owner
    timezone = TimeZone.objects.filter(users=user).first()
    gmt0 = pytz.timezone('GMT')
    date = datetime.now(gmt0).replace(microsecond=0)
    bot_info = f'Bot {bot.pk} {bot.symbol.name}'
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

    in_time = f'{date.time()} | {date.date()}'
    Log.objects.create(bot=bot, content=f'{bot_info} {text}', time=f'{in_time} (GMT {str_gmt})')
