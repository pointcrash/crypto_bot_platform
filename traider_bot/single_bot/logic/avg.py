from api.api_v5_bybit import get_current_price, get_order_status
from bots.bot_logic import get_quantity_from_price, custom_logging
from bots.models import Log
from orders.models import Order


def to_avg_by_grid(bot, side, psn_price, psn_qty):
    current_price = get_current_price(bot.account, bot.category, bot.symbol)
    psn_currency_amount = psn_price * psn_qty / bot.isLeverage
    avg_currency_amount = psn_currency_amount * bot.bb_avg_percent / 100

    if side == "Buy":
        if psn_price - current_price > psn_price * bot.grid_avg_value / 100:
            if bot.max_margin:
                if psn_currency_amount + avg_currency_amount <= bot.max_margin:
                    order = Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side=side,
                        orderType="Market",
                        qty=get_quantity_from_price(avg_currency_amount, current_price, bot.symbol.minOrderQty,
                                                    bot.isLeverage),
                    )

                    custom_logging(bot, f'Position AVG. New Margin -> {round(psn_currency_amount + avg_currency_amount, 2)}')
                    return True
                else:
                    last_log = Log.objects.filter(bot=bot).last()
                    if 'MARGIN LIMIT!' not in last_log.content:
                        custom_logging(bot,
                                f'MARGIN LIMIT! Max margin -> {bot.max_margin}, Margin after avg -> {round(psn_currency_amount + avg_currency_amount, 2)}')
            else:
                order = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    side=side,
                    orderType="Market",
                    qty=get_quantity_from_price(avg_currency_amount, current_price, bot.symbol.minOrderQty,
                                                bot.isLeverage),
                )
        return False

    if side == "Sell":
        if current_price - psn_price > psn_price * bot.grid_avg_value / 100:
            if bot.max_margin:
                if psn_currency_amount + avg_currency_amount <= bot.max_margin:
                    order = Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side=side,
                        orderType="Market",
                        qty=get_quantity_from_price(avg_currency_amount, current_price, bot.symbol.minOrderQty,
                                                    bot.isLeverage),
                    )

                    custom_logging(bot, f'Position AVG. New Margin -> {round(psn_currency_amount + avg_currency_amount, 2)}')
                    return True
                else:
                    last_log = Log.objects.filter(bot=bot).last()
                    if 'MARGIN LIMIT!' not in last_log.content:
                        custom_logging(bot,
                                f'MARGIN LIMIT! Max margin -> {bot.max_margin}, Margin after avg -> {round(psn_currency_amount + avg_currency_amount, 2)}')
            else:
                order = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    side=side,
                    orderType="Market",
                    qty=get_quantity_from_price(avg_currency_amount, current_price, bot.symbol.minOrderQty,
                                                bot.isLeverage),
                )

                custom_logging(bot, f'Position AVG. New Margin -> {round(psn_currency_amount + avg_currency_amount, 2)}')
                return True
        return False


def get_status_avg_order(bot, order):
    status = get_order_status(bot.account, bot.category, bot.symbol, order.order_link_id)
    if status == 'Filled':
        return True
    if status == 'Order does not exist' or status == 'Cancelled':
        order.delete()
        return False


def set_avg_order(bot, side, psn_price, psn_qty):
    psn_currency_amount = psn_price * psn_qty / bot.isLeverage
    avg_currency_amount = psn_currency_amount * bot.bb_avg_percent / 100

    if side == 'Buy':
        avg_price = psn_price - (psn_price * bot.grid_avg_value / 100)
    elif side == 'Sell':
        avg_price = psn_price + (psn_price * bot.grid_avg_value / 100)

    if bot.max_margin and psn_currency_amount + avg_currency_amount > bot.max_margin:
        last_log = Log.objects.filter(bot=bot).last()
        if 'MARGIN LIMIT!' not in last_log.content:
            custom_logging(bot,
                    f'MARGIN LIMIT! Max margin -> {bot.max_margin}, Margin after avg -> {round(psn_currency_amount + avg_currency_amount, 2)}')

        return 'MARGIN LIMIT!'

    else:
        order = Order(
            bot=bot,
            category=bot.category,
            symbol=bot.symbol.name,
            side=side,
            orderType='Limit',
            qty=get_quantity_from_price(avg_currency_amount, avg_price, bot.symbol.minOrderQty, bot.isLeverage),
            price=round(avg_price, int(bot.symbol.priceScale)),
        )

        return order
