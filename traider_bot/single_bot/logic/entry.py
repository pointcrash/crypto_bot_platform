import time

from api_v5 import get_list, get_qty, get_side, get_position_price, cancel_all
from bots.bot_logic import set_entry_point_by_market, entry_order_status_check, logging, set_entry_point, \
    create_bb_and_avg_obj
from bots.models import Take, AvgOrder
from single_bot.logic.avg import to_avg_by_grid, get_status_avg_order, set_avg_order


def entry_position(bot, takes):
    first_cycle = True
    position_idx = 0 if bot.side == 'Buy' else 1
    # bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot, position_idx)

    while True:
        symbol_list = get_list(bot.account, bot.category, bot.symbol)

        if get_qty(symbol_list)[position_idx]:
            psn_qty = get_qty(symbol_list)[position_idx]
            psn_side = get_side(symbol_list)[position_idx]
            psn_price = get_position_price(symbol_list)[position_idx]
            if entry_order_status_check(bot):
                logging(bot, f'position opened. Margin: {psn_qty * psn_price / bot.isLeverage}')

            # if bb_avg_obj:
            #     bb_avg_obj.psn_price = psn_price
            #     bb_avg_obj.psn_side = psn_side
            #     bb_avg_obj.psn_qty = psn_qty

            if bot.auto_avg:
                if bot.work_model == 'grid':
                    avg_order = AvgOrder.objects.filter(bot=bot).first()
                    if not avg_order:
                        avg_order = set_avg_order(bot, psn_side, psn_price, psn_qty)
                        first_cycle = False
                    else:
                        if get_status_avg_order(bot, bot.avgorder):
                            logging(bot,
                                    f'Position AVG. New Margin -> {round(psn_qty * psn_price / bot.isLeverage, 2)}')
                            avg_order.delete()
                            for take in takes:
                                take.order_link_id = ''
                                take.is_filled = False
                            Take.objects.bulk_update(takes, ['order_link_id', 'is_filled'])
                            first_cycle = False
                            continue

                # elif bot.work_model == "bb" and bb_avg_obj is not None:
                #     if bb_avg_obj.auto_avg():
                #         symbol_list = get_list(bot.account, bot.category, bot.symbol)
                #         logging(bot, f'average. New margin: {round(get_qty(symbol_list)[position_idx] * get_position_price(symbol_list)[position_idx] / bot.isLeverage, 2)}')
                #         first_cycle = False
                #         if bot.take1:
                #             bot.take1 = ''
                #             bot.save()
                #         continue

            return psn_qty, psn_side, psn_price, first_cycle, avg_order

        if bot.orderType == "Market":
            set_entry_point_by_market(bot)
            first_cycle = False
            continue

        tl = bb_obj.tl
        bl = bb_obj.bl

        if not first_cycle:
            time.sleep(bot.time_sleep)

        if first_cycle or tl != bb_obj.tl or bl != bb_obj.bl:
            cancel_all(bot.account, bot.category, bot.symbol)
            set_entry_point(bot, tl, bl)

        first_cycle = False
