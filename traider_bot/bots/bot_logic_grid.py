import math
import time
from decimal import Decimal

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from api_v5 import cancel_all
from bots.bot_logic import calculation_entry_point, count_decimal_places
from orders.models import Order


def set_takes_for_grid_bot(bot, bb_obj, bb_avg_obj):
    fraction_length = int(count_decimal_places(Decimal(bot.symbol.minOrderQty)))
    round_number = int(bot.symbol.priceScale)
    set_takes_qty = 0
    while True:
        psn_qty, psn_side, psn_price, first_cycle = calculation_entry_point(bot, bb_obj, bb_avg_obj)

        if first_cycle:  # Not first cycle (-_-)
            time.sleep(bot.time_sleep)

        if (not first_cycle) or set_takes_qty != psn_qty:
            cancel_all(bot.account, bot.category, bot.symbol)

            side = "Buy" if psn_side == "Sell" else "Sell"
            qty = math.floor((psn_qty / 2) * 10 ** fraction_length) / 10 ** fraction_length

            if side == "Buy":
                first_take = round(psn_price - psn_price * bot.grid_profit_value / 100, round_number)
                second_take = round(psn_price - psn_price * (bot.grid_profit_value * 2) / 100, round_number)
            else:
                first_take = round(psn_price + psn_price * bot.grid_profit_value / 100, round_number)
                second_take = round(psn_price + psn_price * (bot.grid_profit_value * 2) / 100, round_number)

            if not qty and psn_qty:
                take1 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    isLeverage=bot.isLeverage,
                    side=side,
                    orderType='Limit',
                    qty=bot.symbol.minOrderQty,
                    price=second_take,
                    is_take=True,
                )
            elif qty and (psn_qty * (10 ** fraction_length)) % 2 == 0:
                take1 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    isLeverage=bot.isLeverage,
                    side=side,
                    orderType='Limit',
                    qty=qty,
                    price=first_take,
                    is_take=True,
                )
                take2 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    isLeverage=bot.isLeverage,
                    side=side,
                    orderType='Limit',
                    qty=qty,
                    price=second_take,
                    is_take=True,
                )
            else:
                take1 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    isLeverage=bot.isLeverage,
                    side=side,
                    orderType='Limit',
                    qty=qty,
                    price=first_take,
                    is_take=True,
                )
                take2 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    isLeverage=bot.isLeverage,
                    side=side,
                    orderType='Limit',
                    qty=(qty + (1 / 10 ** fraction_length)),
                    price=second_take,
                    is_take=True,
                )
            set_takes_qty = psn_qty


