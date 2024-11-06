from datetime import datetime, timedelta
from decimal import ROUND_DOWN

from django.utils import timezone

from api_2.api_bybit import *
from api_2.api_binance import *
from api_2.pybit_api import bybit_place_batch_order, bybit_internal_transfer, bybit_withdraw, bybit_get_user_assets, \
    bybit_get_pnl_by_time, bybit_get_wallet_balance, bybit_get_all_position_info, bybit_get_transaction_log


def get_quantity_from_price(bot, price, amount):
    min_order_qty = Decimal(bot.symbol.minOrderQty)
    result = (Decimal(str(amount * bot.leverage)) / price).quantize(min_order_qty, rounding=ROUND_DOWN)

    custom_logging(bot, f'get_quantity_from_price: amount = {amount}, price = {price},'
                        f' bot.leverage = {bot.leverage}, minOrderQty = {bot.symbol.minOrderQty}, result = {result}')
    return result


def min_qty_check(symbol, leverage, price, amount):
    qty = (Decimal(str(amount * leverage)) / price).quantize(Decimal(symbol.minOrderQty), rounding=ROUND_DOWN)
    if qty < Decimal(symbol.minOrderQty):
        return False
    else:
        return True


def get_all_position_inform(account):
    psn_list = []
    if account.service.name == 'Binance':
        psn_list = binance_get_all_position_inform(account)

    elif account.service.name == 'ByBit':
        psn_list = bybit_get_all_position_info(account)

    for psn in psn_list:
        psn['markPrice'] = str(float(psn['markPrice'])) if psn['markPrice'] else 0
        psn['entryPrice'] = str(float(psn['entryPrice'])) if psn['entryPrice'] else 0
        if psn.get('unrealisedPnl'):
            psn['unrealisedPnl'] = str(round(float(psn['unrealisedPnl']), 2))
        else:
            psn['unrealisedPnl'] = '0'

    return psn_list


def get_position_inform(bot):
    if bot.account.service.name == 'Binance':
        psn_list = binance_get_position_inform(bot)

    elif bot.account.service.name == 'ByBit':
        psn_list = bybit_get_position_inform(bot)

    for psn in psn_list:
        psn['qty'] = psn['qty'] if Decimal(psn['qty']) != 0 else str(Decimal(psn['qty']).normalize())
        psn['markPrice'] = str(float(psn['markPrice'])) if psn['markPrice'] else 0
        psn['entryPrice'] = str(float(psn['entryPrice'])) if psn['entryPrice'] else 0
        if psn.get('unrealisedPnl'):
            psn['unrealisedPnl'] = str(round(float(psn['unrealisedPnl']), 2))
        else:
            psn['unrealisedPnl'] = '0'

    return psn_list


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
        if not amount_usdt:
            raise ValueError('qty or amount must be specified')
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


def change_position_mode(bot, hedge_mode=True):
    if bot.account.service.name == 'Binance':
        return binance_change_position_mode_on_hedge(bot, hedge_mode=hedge_mode)
    elif bot.account.service.name == 'ByBit':
        return bybit_change_position_mode_on_hedge(bot, hedge_mode=hedge_mode)


def get_futures_account_balance(account):
    try:
        if account.service.name == 'Binance':
            return binance_account_balance(account)
        elif account.service.name == 'ByBit':
            return bybit_get_wallet_balance(account)
    except Exception as e:
        raise Exception(e)

    ''' Returned data:
    {   
        'fullBalance': 1454.82,
        'availableBalance': 707.96,
        'unrealizedPnl': -7.96,
    }
    '''


# def fund_account_balance(account):
#     if account.service.name == 'Binance':
#         return binance_account_balance(account)
#     elif account.service.name == 'ByBit':
#         return bybit_account_balance(account)
#
#     ''' Returned data:
#     {
#         'fullBalance': 1454.82,
#         'availableBalance': 707.96,
#     }
#     '''


def get_exchange_information(account, service_name):
    if service_name == 'Binance':
        return get_binance_exchange_information(account)
    elif service_name == 'ByBit':
        return get_bybit_exchange_information(account)


def get_user_assets(account, symbol):
    if account.service.name == 'Binance':
        return binance_get_user_asset(account, symbol)
    elif account.service.name == 'ByBit':
        return bybit_get_user_assets(account, symbol)


def internal_transfer(account, symbol, amount, from_account_type, to_account_type):
    if account.service.name == 'Binance':
        return binance_internal_transfer(account, symbol, amount, from_account_type, to_account_type)
    elif account.service.name == 'ByBit':
        return bybit_internal_transfer(account, symbol, amount, from_account_type, to_account_type)


def withdraw(account, symbol, amount, chain, address):
    if account.service.name == 'Binance':
        return binance_withdraw(account, symbol, amount, chain, address)
    elif account.service.name == 'ByBit':
        return bybit_withdraw(account, symbol, amount, chain, address)


def transaction_history(account, start_time=None, end_time=None):
    if account.service.name == 'Binance':
        return binance_get_income_history(account, start_time=start_time, end_time=start_time)
    elif account.service.name == 'ByBit':
        return bybit_get_transaction_log(account, start_time=start_time, end_time=end_time)


def get_pnl_by_time(bot, start_time, end_time=None):
    get_pnl_func = None

    #  Get 'get_pnl_func'
    if bot.account.service.name == 'Binance':
        get_pnl_func = binance_get_pnl_by_time
    elif bot.account.service.name == 'ByBit':
        get_pnl_func = bybit_get_pnl_by_time

    #  Calculate sum total pnl by time
    if get_pnl_func is not None:
        total_pnl = 0
        if end_time is None:
            end_time = timezone.now()

        custom_logging(bot, end_time)
        custom_logging(bot, start_time)
        while end_time - start_time > timedelta(days=7):
            seven_days_later = start_time + timedelta(days=7)
            pnl = get_pnl_func(bot, start_time, seven_days_later)
            total_pnl += pnl
            start_time = seven_days_later

        if end_time - start_time < timedelta(days=7):
            pnl = get_pnl_func(bot, start_time, end_time)
            total_pnl += pnl

        return str(total_pnl)

