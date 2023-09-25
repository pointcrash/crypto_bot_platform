from decimal import Decimal

from api_v5 import get_current_price, get_list
from bots.bot_logic import get_quantity_from_price, logging
from orders.models import Order


def manual_average_for_simple_hedge(bot, amount, is_percent):
    current_price = get_current_price(bot.account, bot.category, bot.symbol)
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
            logging(bot, f'Позиция {side} усреднена на {amount} USDT = {qty} монет')

    else:
        symbol_list = get_list(bot.account, symbol=bot.symbol)
        if float(symbol_list[0]['size']) != 0 or float(symbol_list[1]['size']) != 0:
            for position_idx in range(1, 3):
                qty = Decimal(symbol_list[position_idx - 1]['size'])
                side = symbol_list[position_idx - 1]['side']
                if qty != 0:
                    decimal_part = str(qty).split('.')[1]
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
                    logging(bot, f'Позиция {side} усреднена на {qty} монет')
                else:
                    logging(bot, f'Попытка усреднить нулевую позицию {side}')
        else:
            logging(bot, f'Нет открытых позиций по данной торговой паре')
