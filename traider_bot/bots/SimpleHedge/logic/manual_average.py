from decimal import Decimal

from api.api_v5_bybit import get_current_price, get_list, cancel_all
from bots.bot_logic import get_quantity_from_price, custom_logging
from orders.models import Order


def manual_average_for_simple_hedge(bot, amount, is_percent, price):
    cancel_all(bot.account, bot.category, bot.symbol)
    current_price = get_current_price(bot.account, bot.category, bot.symbol)

    if price:
        price = Decimal(price)
        first_order_qty = get_quantity_from_price(bot.qty, price, bot.symbol.minOrderQty, bot.isLeverage)
        trigger_direction = 1 if price > current_price else 2

        for order_side in ['Buy', 'Sell']:
            order = Order.objects.create(
                bot=bot,
                category=bot.category,
                symbol=bot.symbol.name,
                side=order_side,
                orderType="Market",
                qty=first_order_qty,
                price=str(price),
                triggerDirection=trigger_direction,
                triggerPrice=str(price),
            )
        return

    amount = Decimal(amount)
    if not is_percent:
        qty = get_quantity_from_price(float(amount), current_price, bot.symbol.minOrderQty, bot.isLeverage)
        for side in ['Buy', 'Sell']:
            order = Order.objects.create(
                bot=bot,
                category=bot.category,
                symbol=bot.symbol.name,
                side=side,
                orderType="Market",
                qty=qty,
            )
            custom_logging(bot, f'Позиция {side} усреднена на {amount} USDT = {qty} монет')

    else:
        symbol_list = get_list(bot.account, symbol=bot.symbol)
        if float(symbol_list[0]['size']) != 0 or float(symbol_list[1]['size']) != 0:
            for position_idx in range(1, 3):
                qty = Decimal(symbol_list[position_idx - 1]['size'])
                side = symbol_list[position_idx - 1]['side']
                if qty != 0:
                    try:
                        decimal_part = str(qty).split('.')[1]
                    except:
                        decimal_part = []
                    decimal_places = len(decimal_part)
                    qty = round(qty * amount / 100, decimal_places)
                    order = Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side=side,
                        orderType="Market",
                        qty=qty,
                    )
                    custom_logging(bot, f'Позиция {side} усреднена на {qty} монет')
                else:
                    custom_logging(bot, f'Попытка усреднить нулевую позицию {side}')
        else:
            custom_logging(bot, f'Нет открытых позиций по данной торговой паре')
