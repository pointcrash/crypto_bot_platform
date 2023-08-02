from api_v5 import get_list, get_qty, get_current_price
from bots.bot_logic import get_quantity_from_price, logging
from orders.models import Order


def set_entry_point_by_market_for_hedge(bot):
    symbol_list = get_list(bot.account, bot.category, bot.symbol)
    qty_list = get_qty(symbol_list)
    if qty_list[0] or qty_list[1]:
        return None

    round_number = int(bot.symbol.priceScale)
    current_price = get_current_price(bot.account, bot.category, bot.symbol)
    tp_list = []

    for side in ['Buy', 'Sell']:
        if side == 'Buy':
            tp_limit_price = round(current_price * (1 + bot.grid_profit_value / 100), round_number)
            tp_list.append(tp_limit_price)
        else:
            tp_limit_price = round(current_price * (1 - bot.grid_profit_value / 100), round_number)
            tp_list.append(tp_limit_price)

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

    return tuple(tp_list)
