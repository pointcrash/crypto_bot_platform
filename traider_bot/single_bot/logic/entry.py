import time

from api_v5 import get_list, get_qty, get_side, get_position_price, cancel_all
from bots.bot_logic import set_entry_point_by_market, entry_order_status_check, logging, set_entry_point, \
    create_bb_and_avg_obj
from bots.models import Take, AvgOrder
from single_bot.logic.avg import to_avg_by_grid, get_status_avg_order, set_avg_order
from single_bot.logic.global_variables import lock, global_list_bot_id


def entry_position(bot, takes, position_idx):
    bot_id = bot.pk
    first_cycle = True

    bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot, position_idx)
    avg_order = None

    if bb_obj:
        tl = bb_obj.tl
        bl = bb_obj.bl

    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            if lock.locked():
                lock.release()
            symbol_list = get_list(bot.account, bot.category, bot.symbol)
            if position_idx is None:
                position_idx = get_position_idx_by_range(symbol_list)

            if position_idx is not None and get_qty(symbol_list)[position_idx]:
                psn_qty = get_qty(symbol_list)[position_idx]
                psn_side = get_side(symbol_list)[position_idx]
                psn_price = get_position_price(symbol_list)[position_idx]
                if entry_order_status_check(bot):
                    logging(bot, f'position opened. Margin: {psn_qty * psn_price / bot.isLeverage}')

                if bot.auto_avg:
                    if bot.work_model == 'grid':
                        avg_order = AvgOrder.objects.filter(bot=bot).first()
                        if not avg_order:
                            avg_order = set_avg_order(bot, psn_side, psn_price, psn_qty)
                            first_cycle = False
                        else:
                            if get_status_avg_order(bot, avg_order):
                                logging(bot,
                                        f'Position AVG. New Margin -> {round(psn_qty * psn_price / bot.isLeverage, 2)}')
                                avg_order.delete()
                                for take in takes:
                                    take.order_link_id = ''
                                    take.is_filled = False
                                Take.objects.bulk_update(takes, ['order_link_id', 'is_filled'])
                                first_cycle = False
                                continue

                return psn_qty, psn_side, psn_price, first_cycle, avg_order

            if bot.orderType == "Market":
                set_entry_point_by_market(bot)
                first_cycle = False
                time.sleep(1)
                continue

            if not first_cycle:
                flag = False
                waiting_time = bot.time_sleep
                seconds = 1
                while seconds < waiting_time:
                    lock.acquire()
                    try:
                        if bot_id not in global_list_bot_id:
                            flag = True
                            seconds = waiting_time
                    finally:
                        if lock.locked():
                            lock.release()
                    if seconds < waiting_time:
                        time.sleep(2)
                        seconds += 2
                if flag:
                    continue

            if first_cycle or tl != bb_obj.tl or bl != bb_obj.bl:
                cancel_all(bot.account, bot.category, bot.symbol)
                tl = bb_obj.tl
                bl = bb_obj.bl
                set_entry_point(bot, tl, bl)

            time.sleep(1)
            first_cycle = False
            lock.acquire()
    finally:
        if lock.locked():
            lock.release()


def get_position_idx_by_range(symbol_list):
    for i in range(2):
        if get_qty(symbol_list)[i]:
            return i
    return None
