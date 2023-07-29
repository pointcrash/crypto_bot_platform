import math
import time
from decimal import Decimal

from api_v5 import switch_position_mode, set_leverage, cancel_all
from bots.bot_logic import count_decimal_places, logging
from bots.bot_logic_grid import take_status_check
from bots.models import Take, AvgOrder, SingleBot, Process
from bots.terminate_bot_logic import stop_bot_with_cancel_orders
from orders.models import Order
from single_bot.logic.entry import entry_position
from single_bot.logic.global_variables import global_list_threads, lock


def bot_work_logic(bot):
    bot_id = bot.pk
    is_ts_bot = True if bot.side == 'TS' else False

    position_idx = get_position_idx(bot.side)
    append_thread_or_check_duplicate(bot_id, is_ts_bot)

    new_cycle = True
    if not is_ts_bot:
        switch_position_mode(bot)
        set_leverage(bot.account, bot.category, bot.symbol, bot.isLeverage)
    fraction_length = int(count_decimal_places(Decimal(bot.symbol.minOrderQty)))
    round_number = int(bot.symbol.priceScale)

    lock.acquire()
    try:
        while bot_id in global_list_threads:
            lock.release()

            takes = get_takes(bot)
            if not new_cycle:
                for take in takes:
                    if not take.is_filled:
                        take_status = take_status_check(bot, take)
                        if take_status:
                            take.is_filled = take_status
                            logging(bot, f'take_{take.take_number} is filled.')
                Take.objects.bulk_update(takes, ['is_filled'])

                if all(take.is_filled for take in takes):
                    logging(bot, f'bot finished cycle. P&L: {bot.pnl}')
                    if not bot.repeat:
                        stop_bot_with_cancel_orders(bot)
                        break

            takes = get_takes(bot)

            psn_qty, psn_side, psn_price, first_cycle, avg_order = entry_position(bot, takes, position_idx)

            takes = get_takes(bot)

            if first_cycle and new_cycle is False:  # Not first cycle (-_-)
                time.sleep(bot.time_sleep)

            if not first_cycle or new_cycle is True:
                new_cycle = False
                cancel_all(bot.account, bot.category, bot.symbol)

                side = "Buy" if psn_side == "Sell" else "Sell"
                qty = Decimal(math.floor((psn_qty / bot.grid_take_count) * 10 ** fraction_length) / 10 ** fraction_length)
                oli_list = []

                for i, take in enumerate(takes, start=1):
                    if side == "Buy":
                        price = round(psn_price - psn_price * bot.grid_profit_value * i / 100, round_number)
                    elif side == "Sell":
                        price = round(psn_price + psn_price * bot.grid_profit_value * i / 100, round_number)

                    if not take.is_filled:
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
                else:
                    print(type(avg_order), avg_order)
            lock.acquire()
    finally:
        lock.release()


def get_takes(bot):
    takes = Take.objects.filter(bot=bot)

    if not takes:
        takes_to_create = [
            Take(bot=bot, take_number=i+1) for i in range(bot.grid_take_count)
        ]
        Take.objects.bulk_create(takes_to_create)
        return Take.objects.filter(bot=bot)
    else:
        return takes


def get_position_idx(side):
    if side == 'FB' or side == 'TS':
        position_idx = None
    else:
        position_idx = 0 if side == 'Buy' else 1

    return position_idx


def append_thread_or_check_duplicate(bot_id, is_ts_bot):
    lock.acquire()
    try:
        if bot_id not in global_list_threads:
            global_list_threads.add(bot_id)
        elif is_ts_bot:
            pass
        else:
            # global_list_threads.remove(bot_id)
            raise Exception("Duplicate bot")
    finally:
        lock.release()
