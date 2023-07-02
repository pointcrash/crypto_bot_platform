import math
import time
from decimal import Decimal, ROUND_DOWN

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from api_v5 import cancel_all
from bots.bot_logic import calculation_entry_point, count_decimal_places
from orders.models import Order


def set_takes_for_grid_bot(bot):
    fraction_length = int(count_decimal_places(Decimal(bot.symbol.minOrderQty)))
    round_number = int(bot.symbol.priceScale)
    set_takes_qty = 0
    while True:
        psn_qty, psn_side, psn_price, BB_obj, first_cycle = calculation_entry_point(bot)

        if first_cycle:  # Not first cycle (-_-)
            time.sleep(10)

        if (not first_cycle) or set_takes_qty != psn_qty:
            print('Вошли в выставление тейков')
            cancel_all(bot.account, bot.category, bot.symbol)

            side = "Buy" if psn_side == "Sell" else "Sell"
            qty = math.floor((psn_qty / 2) * 10 ** fraction_length) / 10 ** fraction_length
            print(side)
            print(qty)

            if side == "Buy":
                first_take = round(psn_price - psn_price * Decimal('0.01'), round_number)
                second_take = round(psn_price - psn_price * Decimal('0.02'), round_number)
            else:
                first_take = round(psn_price + psn_price * Decimal('0.01'), round_number)
                second_take = round(psn_price + psn_price * Decimal('0.02'), round_number)

            if not qty and psn_qty:
                print(1)
                take1 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    side=side,
                    orderType='Limit',
                    qty=bot.symbol.minOrderQty,
                    price=second_take,
                    is_take=True,
                )
            elif qty and (psn_qty * (10 ** fraction_length)) % 2 == 0:
                print(2)
                take1 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
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
                    side=side,
                    orderType='Limit',
                    qty=qty,
                    price=second_take,
                    is_take=True,
                )
            else:
                print(3)
                take1 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
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
                    side=side,
                    orderType='Limit',
                    qty=(qty + (1 / 10 ** fraction_length)),
                    price=second_take,
                    is_take=True,
                )
            set_takes_qty = psn_qty
