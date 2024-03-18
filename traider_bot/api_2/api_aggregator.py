from decimal import ROUND_DOWN

from api_2.api_bybit import *
from api_2.api_binance import *
from api_2.pybit_api import bybit_place_batch_order


def get_quantity_from_price(bot, price, amount):
    return (Decimal(str(amount * bot.isLeverage)) / price).quantize(Decimal(bot.symbol.minOrderQty), rounding=ROUND_DOWN)


def get_position_inform(bot):
    if bot.account.service.name == 'Binance':
        return binance_get_position_inform(bot)

    elif bot.account.service.name == 'ByBit':
        return bybit_get_position_inform(bot)

    ''' Returned data:
        [{'symbol': 'BTCUSDT',
        'qty': '0.02',
        'entryPrice': '43257.245100',
        'markPrice': '41257.282100',
        'unrealisedPnl': '-13.542300',
        'side': 'LONG'},
        {'symbol': 'BTCUSDT',
        'qty': '0.00',
        'entryPrice': '0',
        'markPrice': '0',
        'unrealisedPnl': '0',
        'side': 'SHORT'}]
    '''


def place_order(bot, side, order_type, price, amount_usdt=None, qty=None, position_side=None, timeInForce=None):
    if order_type.upper() == 'LIMIT' and not timeInForce:
        timeInForce = 'GTC'
    if not qty:
        amount_usdt = bot.qty if not amount_usdt else amount_usdt
        qty = get_quantity_from_price(bot, price, amount_usdt)

    if bot.account.service.name == 'Binance':
        return binance_place_order(bot=bot, side=side, order_type=order_type,
                                   price=price, qty=qty, position_side=position_side, timeInForce=timeInForce)
    elif bot.account.service.name == 'ByBit':
        return bybit_place_order(bot=bot, side=side, order_type=order_type,
                                 price=price, qty=qty, position_side=position_side)


def place_batch_order(bot, order_list):

    # Используем цену для расчета qty если оно не передано
    for order in order_list:
        if not order.get('qty') and order.get('price'):
            order['qty'] = str(get_quantity_from_price(bot, price=Decimal(order['price']), amount=bot.qty))

            # Удаляем параметр price если это маркет-ордер
            if order['type'].upper() == 'MARKET':
                order.pop('price')

    if bot.account.service.name == 'Binance':
        return binance_place_batch_order(bot, order_list)
    elif bot.account.service.name == 'ByBit':
        return bybit_place_batch_order(bot, order_list)


def cancel_all_orders(bot):
    if bot.account.service.name == 'Binance':
        return binance_cancel_all_orders(bot)
    elif bot.account.service.name == 'ByBit':
        return bybit_cancel_all_orders(bot)


def cancel_order(bot, order_id):
    if bot.account.service.name == 'Binance':
        return binance_cancel_order(bot, order_id)
    elif bot.account.service.name == 'ByBit':
        return bybit_cancel_order(bot, order_id)


def get_open_orders(bot):
    if bot.account.service.name == 'Binance':
        return binance_get_open_orders(bot)
    elif bot.account.service.name == 'ByBit':
        return bybit_get_open_orders(bot)


def get_current_price(bot):
    if bot.account.service.name == 'Binance':
        return binance_get_current_price(bot)
    elif bot.account.service.name == 'ByBit':
        return bybit_get_current_price(bot)


def set_leverage(bot):
    if bot.account.service.name == 'Binance':
        return binance_set_leverage(bot)
    elif bot.account.service.name == 'ByBit':
        return bybit_set_leverage(bot)


def change_position_mode(bot):
    if bot.account.service.name == 'Binance':
        return binance_change_position_mode_on_hedge(bot)
    elif bot.account.service.name == 'ByBit':
        return bybit_change_position_mode_on_hedge(bot)


def account_balance(bot):
    if bot.account.service.name == 'Binance':
        return binance_account_balance(bot)
    elif bot.account.service.name == 'ByBit':
        return bybit_account_balance(bot)

    ''' Returned data:
    {   
        'fullBalance': 1454.82,
        'availableBalance': 707.96,
    }
    '''
