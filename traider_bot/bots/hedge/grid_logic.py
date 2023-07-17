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

    while True:
        time.sleep(bot.time_sleep)
        symbol_list = get_list(bot.account, bot.category, bot.symbol)
        price_list = get_position_price(symbol_list)
        qty_list = get_qty(symbol_list)
        if price_list[0] or price_list[1]:
            current_price = get_current_price(bot.account, bot.category, bot.symbol)
            if qty_list[0] * current_price * 2 / bot.isLeverage >= bot.max_margin or qty_list[1] * current_price * 2 / bot.isLeverage >= bot.max_margin:
                logging(bot, f'MARGIN LIMIT')
                break
            else:
                if current_price < price_list[0] * (1 - bot.grid_profit_value / 100):
                    Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side='Buy',
                        orderType='Market',
                        qty=get_quantity_from_price(qty_list[0] * price_list[0] / bot.isLeverage, current_price,
                                                    bot.symbol.minOrderQty, bot.isLeverage),
                        takeProfit=str(current_price * (1 + bot.grid_profit_value / 100)),

                    )
                    logging(bot, f'create AVG order. Side: "Buy". Margin: {qty_list[0] * price_list[0]}')

                elif current_price > price_list[1] * (1 + bot.grid_profit_value / 100):
                    Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side='Sell',
                        orderType='Market',
                        qty=get_quantity_from_price(qty_list[1] * price_list[1] / bot.isLeverage, current_price,
                                                    bot.symbol.minOrderQty, bot.isLeverage),
                        takeProfit=str(current_price * (1 - bot.grid_profit_value / 100)),

                    )
                    logging(bot,
                            f'create AVG order. Side: "Sell". Margin: {qty_list[1] * price_list[1]}\n TP: {current_price * (1 - bot.grid_profit_value / 100)}')


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
    current_price = get_current_price(bot.account, bot.category, bot.symbol)
    for side in ['Buy', 'Sell']:
        if side == 'Buy':
            tp_limit_price = current_price * (1 + bot.grid_profit_value / 100)
        else:
            tp_limit_price = current_price * (1 - bot.grid_profit_value / 100)

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
