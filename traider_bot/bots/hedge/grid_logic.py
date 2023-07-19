import math
import time
from decimal import Decimal

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from api_v5 import get_order_status, get_pnl, set_leverage, switch_position_mode, get_list, get_qty, \
    get_position_price, get_current_price
from bots.bot_logic import count_decimal_places, logging, get_quantity_from_price
from orders.models import Order


def set_takes_for_hedge_grid_bot(bot):
    switch_position_mode(bot)
    set_leverage(bot.account, bot.category, bot.symbol, bot.isLeverage)
    fraction_length = int(count_decimal_places(Decimal(bot.symbol.minOrderQty)))
    round_number = int(bot.symbol.priceScale)
    set_entry_point_by_market_for_hedge(bot)

    start_time = int(time.time()) * 1000
    start_pnl_list = []
    total_pnl = 0
    ml0 = 0
    ml1 = 0

    while True:
        time.sleep(bot.time_sleep)
        symbol_list = get_list(bot.account, bot.category, bot.symbol)
        price_list = get_position_price(symbol_list)
        qty_list = get_qty(symbol_list)

        new_pnl_list = get_pnl(bot.account, bot.category, bot.symbol.name, start_time)
        if start_pnl_list != new_pnl_list:
            total_pnl += Decimal(new_pnl_list[0]["closedPnl"])
            logging(bot, f'TP IS SUCCESS. Side: {new_pnl_list[0]["side"]} PNL: {round(Decimal(new_pnl_list[0]["closedPnl"]), 2)}')
            start_pnl_list = new_pnl_list

        if not qty_list[0] and not qty_list[1]:
            logging(bot, f'Bot finished work. Total PNL: {total_pnl}')
            break

        if qty_list[0]:
            current_price = get_current_price(bot.account, bot.category, bot.symbol)
            margin_after_avg = qty_list[0] * price_list[0] / bot.isLeverage * (1 + bot.bb_avg_percent / 100)

            if margin_after_avg > bot.max_margin:
                if ml0 != 1:
                    logging(bot, f'MARGIN LIMIT -> {bot.max_margin}, margin after avg -> {round(margin_after_avg, 2)}')
                    ml0 = 1
            else:
                if current_price < price_list[0] * (1 - bot.grid_profit_value / 100):
                    qty = get_quantity_from_price(qty_list[0] * price_list[0] / bot.isLeverage, current_price,
                                                  bot.symbol.minOrderQty, bot.isLeverage) * bot.bb_avg_percent / 100
                    avg_price = (qty_list[0] * price_list[0] + qty * current_price) / (qty_list[0] + qty)
                    Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side='Buy',
                        orderType='Market',
                        qty=qty,
                        takeProfit=str(round(avg_price * (1 + bot.grid_profit_value / 100), round_number)),

                    )
                    logging(bot,
                            f'create AVG order. Side: "Buy". Margin: {round(qty_list[0] * price_list[0] / bot.isLeverage * (1 + bot.bb_avg_percent / 100), 2)} TP: {round(avg_price * (1 + bot.grid_profit_value / 100), round_number)}')

        if qty_list[1]:
            current_price = get_current_price(bot.account, bot.category, bot.symbol)
            margin_after_avg = qty_list[1] * price_list[1] / bot.isLeverage * (1 + bot.bb_avg_percent / 100)

            if margin_after_avg > bot.max_margin:
                if ml1 != 1:
                    logging(bot, f'MARGIN LIMIT -> {bot.max_margin}, margin after avg -> {margin_after_avg}')
                    ml1 = 1
            else:
                if current_price > price_list[1] * (1 + bot.grid_profit_value / 100):
                    qty = get_quantity_from_price(qty_list[1] * price_list[1] / bot.isLeverage, current_price,
                                                  bot.symbol.minOrderQty, bot.isLeverage) * bot.bb_avg_percent / 100
                    avg_price = (qty_list[1] * price_list[1] + qty * current_price) / (qty_list[1] + qty)
                    Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side='Sell',
                        orderType='Market',
                        qty=qty,
                        takeProfit=str(round(avg_price * (1 - bot.grid_profit_value / 100), round_number)),

                    )
                    logging(bot,
                            f'create AVG order. Side: "Sell". Margin: {round(qty_list[1] * price_list[1] / bot.isLeverage * (1 + bot.bb_avg_percent / 100), 2)} TP: {round(avg_price * (1 - bot.grid_profit_value / 100), round_number)}')


def take_status_check(bot, orderLinkId):
    if orderLinkId == 'Filled':
        return 'Filled'
    if orderLinkId:
        status = get_order_status(bot.account, bot.category, bot.symbol, orderLinkId)
        if status == 'Filled':
            pnl = get_pnl(bot.account, bot.category, bot.symbol)
            bot.pnl += Decimal(pnl)
            logging(bot, f'take filled. P&L: {pnl}')
            return 'Filled'


def set_entry_point_by_market_for_hedge(bot):
    round_number = int(bot.symbol.priceScale)
    current_price = get_current_price(bot.account, bot.category, bot.symbol)
    for side in ['Buy', 'Sell']:
        if side == 'Buy':
            tp_limit_price = round(current_price * (1 + bot.grid_profit_value / 100), round_number)
        else:
            tp_limit_price = round(current_price * (1 - bot.grid_profit_value / 100), round_number)

        order = Order.objects.create(
            bot=bot,
            category=bot.category,
            symbol=bot.symbol.name,
            side=side,
            orderType='Market',
            qty=get_quantity_from_price(bot.qty, current_price, bot.symbol.minOrderQty, bot.isLeverage),
            takeProfit=str(tp_limit_price),
        )

        logging(bot, f'create order by market. Side: "{side}". Margin: {bot.qty}. TP: {tp_limit_price}')
        if bot.side == 'Sell':
            bot.entry_order_sell = order.orderLinkId
            bot.save()
        else:
            bot.entry_order_by = order.orderLinkId
            bot.save()


def calculation_entry_point_by_hedge(bot):
    set_entry_point_by_market_for_hedge(bot)
