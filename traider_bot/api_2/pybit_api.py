import datetime
import json
import time
import uuid

from pybit.unified_trading import HTTP

from api_2.custom_logging_api import custom_logging


def get_session(account):
    session = HTTP(
        testnet=not account.is_mainnet,
        demo=account.is_demonet,
        api_key=account.API_TOKEN,
        api_secret=account.SECRET_KEY,
    )

    return session


def bybit_set_trading_stop(bot, psn_side, tp_limit_price=None, sl_limit_price=None,
                           tp_size=None, sl_size=None, take_profit_qty=None, stop_loss_qty=None):
    session = get_session(bot.account)
    tpsl_mode = "Full" if not take_profit_qty and not stop_loss_qty else 'Partial'
    position_idx = 1 if psn_side == 'LONG' else 2

    response = session.set_trading_stop(
        category="linear",
        symbol=bot.symbol,
        takeProfit=take_profit_qty,
        stopLoss=stop_loss_qty,
        tpTriggerBy="MarkPrice",
        slTriggerB="MarkPrice",
        tpslMode=tpsl_mode,
        tpSize=tp_size,
        slSize=sl_size,
        tpLimitPrice=tp_limit_price,
        slLimitPrice=sl_limit_price,
        positionIdx=position_idx,
    )
    return response


def bybit_place_batch_order(bot, order_list):
    category = bot.category
    formatted_order_list = []
    for order in order_list:
        formatted_order = {
            "category": category,
            "symbol": order['symbol'],
            "orderType": order['type'].capitalize(),
            "side": order['side'].capitalize(),
            "positionIdx": 1 if order['positionSide'] == 'LONG' else 2,
            "qty": order['qty'],
        }
        if formatted_order['orderType'] == 'Limit':
            formatted_order['price'] = order['price']
        formatted_order_list.append(formatted_order)

    session = get_session(bot.account)
    response = session.place_batch_order(category=category, request=formatted_order_list)
    return response['result']['list']


def bybit_internal_transfer(account, symbol, amount, from_account_type, to_account_type):
    session = get_session(account)

    response = session.create_internal_transfer(
        transferId=str(uuid.uuid4()),
        coin=symbol,
        amount=str(amount),
        fromAccountType=from_account_type,
        toAccountType=to_account_type,
    )
    return response


def bybit_get_all_position_info(account):
    session = get_session(account)

    def format_data(position_list):
        position_inform_list = [{
            'symbol': position['symbol'],
            'qty': position['size'],
            'entryPrice': position['avgPrice'],
            'markPrice': position['markPrice'],
            'unrealisedPnl': position['unrealisedPnl'],
            'side': 'LONG' if int(position['positionIdx']) == 1 else 'SHORT',
        } for position in position_list]
        return position_inform_list

    response = session.get_positions(category='linear', settleCoin='USDT')
    position_inform_list = format_data(response['result']['list'])
    return position_inform_list


def bybit_withdraw(account, symbol, chain, address, amount):
    session = get_session(account)

    response = session.withdraw(
        coin=symbol,
        chain=chain,
        address=address,
        amount=amount,
        accountType="FUND",
        timestamp=int(time.time()) * 1000,
    )
    return response


def bybit_get_user_assets(account, symbol, acc_type="FUND"):
    session = get_session(account)

    response = session.get_coin_balance(
        accountType=acc_type,
        coin=symbol,
    )

    return response['result']['balance']['walletBalance']


def bybit_get_wallet_balance(account, symbol='USDT', acc_type="UNIFIED"):
    session = get_session(account)

    response = session.get_wallet_balance(
        accountType=acc_type,
        coin=symbol,
    )

    response = response['result']['list'][0]
    response = {
        'fullBalance': round(float(response['totalMarginBalance']), 2),
        'availableBalance': round(float(response['totalAvailableBalance']), 2),
        'unrealizedPnl': round(float(response['totalPerpUPL']), 2),
    }

    return response


def bybit_get_pnl_by_time(bot, start_time, end_time):
    session = get_session(bot.account)
    start_time = int(start_time.timestamp() * 1000)
    end_time = int(end_time.timestamp() * 1000)
    total_pnl = 0

    custom_logging(bot, f'bybit_get_pnl_by_time({bot.symbol.name}, {start_time}, {end_time}, )', 'REQUEST')
    response = session.get_closed_pnl(
        category="linear",
        symbol=bot.symbol,
        startTime=start_time,
        endTime=end_time,
    )

    custom_logging(bot, response, 'RESPONSE')
    for trade in response['result']['list']:
        total_pnl += float(trade['closedPnl'])

    return total_pnl


def bybit_get_transaction_log(account, symbol='USDT', acc_type="UNIFIED", start_time=None, end_time=None):
    ''' startTime & endTime must be (ms) '''

    session = get_session(account)

    if not start_time or not end_time:
        response = session.get_transaction_log(accountType=acc_type, currency=symbol)
    else:
        response = session.get_transaction_log(accountType=acc_type, currency=symbol, startTime=start_time, endTime=end_time)

    result_list = response['result']['list']

    def formatter(data: dict) -> dict:
        formatted_data = {
            'symbol': data['symbol'],
            'side': data['side'],
            'orderId': data['orderId'],
            'change': data['change'],
            'cashFlow': data['cashFlow'],
            'fee': data['fee'],
            'transactionTime': data['transactionTime'],
            'type': data['type'],
        }

        return formatted_data

    transaction_log = [formatter(data) for data in result_list]

    return transaction_log


if __name__ == "__main__":
    test_session = HTTP(
        testnet=True,
        api_key="dMwQJxAlfO7Qvl848e",
        api_secret="QrN3JS2VCXwVjV76sHAMwUJFa81KrPMSA0yl",
    )
