from decimal import ROUND_DOWN

from api_2.api_bybit import *
from api_2.api_binance import *
from api_2.pybit_api import bybit_place_batch_order


def get_quantity_from_price(bot, price, amount):
    return (Decimal(str(amount * bot.leverage)) / price).quantize(Decimal(bot.symbol.minOrderQty), rounding=ROUND_DOWN)


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
        qty = get_quantity_from_price(bot, price, amount_usdt)

    if bot.account.service.name == 'Binance':
        return binance_place_order(bot=bot, side=side, order_type=order_type,
                                   price=price, qty=qty, position_side=position_side, timeInForce=timeInForce)
    elif bot.account.service.name == 'ByBit':
        return bybit_place_order(bot=bot, side=side, order_type=order_type,
                                 price=price, qty=qty, position_side=position_side)


def place_conditional_order(bot, side, position_side, trigger_price, trigger_direction, qty=None, amount_usdt=None):
    if not qty:
        qty = get_quantity_from_price(bot, trigger_price, amount_usdt)

    if bot.account.service.name == 'Binance':
        return binance_place_conditional_order(bot=bot, side=side, position_side=position_side,
                                               trigger_price=trigger_price, trigger_direction=trigger_direction,
                                               qty=qty)
    elif bot.account.service.name == 'ByBit':
        return bybit_place_conditional_order(bot=bot, side=side, position_side=position_side,
                                             trigger_price=trigger_price, trigger_direction=trigger_direction, qty=qty)


def place_batch_order(bot, order_list):
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


def get_exchange_information(account, service_name):
    if service_name == 'Binance':
        return get_binance_exchange_information(account)
    elif service_name == 'ByBit':
        return get_bybit_exchange_information(account)
