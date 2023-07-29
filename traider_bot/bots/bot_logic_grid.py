import math
import time
from decimal import Decimal

import os
import django
from django.db import connections

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from api_v5 import cancel_all, get_order_status, get_pnl, set_leverage, switch_position_mode
from bots.bot_logic import calculation_entry_point, count_decimal_places, logging
from orders.models import Order


def set_takes_for_grid_bot(bot, bb_obj, bb_avg_obj):
    new_cycle = True
    switch_position_mode(bot)
    set_leverage(bot.account, bot.category, bot.symbol, bot.isLeverage)
    fraction_length = int(count_decimal_places(Decimal(bot.symbol.minOrderQty)))
    round_number = int(bot.symbol.priceScale)
    take_list = ['' for _ in range(bot.grid_take_count)]

    while True:
        psn_qty, psn_side, psn_price, first_cycle, take_list = calculation_entry_point(bot, bb_obj, bb_avg_obj,
                                                                                       grid_take_list=take_list)

        if first_cycle and new_cycle is False:  # Not first cycle (-_-)
            time.sleep(bot.time_sleep)

        if not first_cycle or new_cycle is True:
            new_cycle = False
            cancel_all(bot.account, bot.category, bot.symbol)

            side = "Buy" if psn_side == "Sell" else "Sell"
            qty = Decimal(math.floor((psn_qty / bot.grid_take_count) * 10 ** fraction_length) / 10 ** fraction_length)

            for i in range(1, bot.grid_take_count + 1):
                if side == "Buy":
                    price = round(psn_price - psn_price * bot.grid_profit_value * i / 100, round_number)
                else:
                    price = round(psn_price + psn_price * bot.grid_profit_value * i / 100, round_number)

                if not take_status_check(bot, take_list[i - 1]):
                    if i == bot.grid_take_count:
                        take = Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            # isLeverage=bot.isLeverage,
                            side=side,
                            orderType='Limit',
                            qty=round(psn_qty, round_number),
                            price=price,
                            is_take=True,
                        )

                        take_list[i-1] = take.orderLinkId
                        logging(bot, f'created take_{i} Price:{price}')

                    else:
                        take = Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            # isLeverage=bot.isLeverage,
                            side=side,
                            orderType='Limit',
                            qty=round(qty, round_number),
                            price=price,
                            is_take=True,
                        )
                        take_list[i-1] = take.orderLinkId
                        logging(bot, f'created take_{i} Price:{price}')

                        psn_qty = psn_qty - qty

                else:
                    logging(bot, f'take_{i} is filled.')
                    take_list[i - 1] = 'Filled'


def take_status_check(bot, take):
    if take.is_filled:
        return True
    if take.order_link_id:
        status = get_order_status(bot.account, bot.category, bot.symbol, take.order_link_id)
        if status == 'Filled':
            pnl = round(Decimal(get_pnl(bot.account, bot.category, bot.symbol)[0]["closedPnl"]), 2)
            bot.pnl = bot.pnl + pnl
            bot.save()
            return True
    return False
