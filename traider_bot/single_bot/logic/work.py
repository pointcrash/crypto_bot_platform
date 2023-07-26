import math
import time
from decimal import Decimal

from api_v5 import switch_position_mode, set_leverage, cancel_all
from bots.bot_logic import count_decimal_places, logging
from bots.bot_logic_grid import take_status_check
from bots.models import Take, AvgOrder, SingleBot
from orders.models import Order
from single_bot.logic.entry import entry_position


def bot_work_logic(bot):
    SingleBot.objects.create(bot=bot, single=True)
    new_cycle = True
    switch_position_mode(bot)
    set_leverage(bot.account, bot.category, bot.symbol, bot.isLeverage)
    fraction_length = int(count_decimal_places(Decimal(bot.symbol.minOrderQty)))
    round_number = int(bot.symbol.priceScale)

    while True:
        takes = get_takes(bot)
        if not new_cycle:
            for take in takes:
                if not take.is_filled:
                    take_status = take_status_check(bot, take)
                    take.is_filled = take_status
                    if take_status:
                        logging(bot, f'take_{take.take_number} is filled.')
            Take.objects.bulk_update(takes, ['is_filled'])

            if all(take.is_filled for take in takes):
                logging(bot, f'bot finished work. P&L: {bot.pnl}')
                if not bot.repeat:
                    break

        psn_qty, psn_side, psn_price, first_cycle, avg_order = entry_position(bot, takes)

        if first_cycle and new_cycle is False:  # Not first cycle (-_-)
            time.sleep(bot.time_sleep)

        if not first_cycle or new_cycle is True:
            new_cycle = False
            cancel_all(bot.account, bot.category, bot.symbol)

            side = "Buy" if psn_side == "Sell" else "Sell"
            qty = Decimal(math.floor((psn_qty / bot.grid_take_count) * 10 ** fraction_length) / 10 ** fraction_length)
            oli_list = []

            for i in range(1, bot.grid_take_count + 1):
                if side == "Buy":
                    price = round(psn_price - psn_price * bot.grid_profit_value * i / 100, round_number)
                elif side == "Sell":
                    price = round(psn_price + psn_price * bot.grid_profit_value * i / 100, round_number)
                if not takes[i-1].is_filled:
                    if i == bot.grid_take_count:
                        order = Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            side=side,
                            orderType='Limit',
                            qty=round(psn_qty, round_number),
                            price=price,
                            is_take=True,
                        )
                        oli_list.append(order.orderLinkId)
                        logging(bot, f'created take_{i} Price:{price}')

                    else:
                        order = Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            side=side,
                            orderType='Limit',
                            qty=round(qty, round_number),
                            price=price,
                            is_take=True,
                        )

                        oli_list.append(order.orderLinkId)
                        logging(bot, f'created take_{i} Price:{price}')

                        psn_qty = psn_qty - qty

            for take, oli in zip(takes, oli_list):
                take.order_link_id = oli
            Take.objects.bulk_update(takes, ['order_link_id'])
            if avg_order is not None and type(avg_order) == Order:
                avg_order.save()
                AvgOrder.objects.create(bot=bot, order_link_id=avg_order.orderLinkId)


def get_takes(bot):
    takes = Take.objects.filter(bot=bot)

    if not takes:
        takes_to_create = [
            Take(bot=bot, take_number=i+1) for i in range(bot.grid_take_count)
        ]
        Take.objects.bulk_create(takes_to_create)

    return Take.objects.filter(bot=bot)

