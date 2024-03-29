import json
import uuid
from decimal import Decimal

from api_test.api_v5_bybit import HTTP_Request
from bots.general_functions import get_quantity_from_price
from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message
from binance.client import Client


def cancel_all(bot, account, category, symbol):
    if bot.service == 'Binance':
        client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)

        client.futures_cancel_all_open_orders(symbol=symbol)  # Отменит все ордера

        pass
    elif bot.service == 'ByBit':
        endpoint = "/v5/order/cancel-all"
        method = "POST"
        params = {
            'category': category,
            'symbol': symbol.name,
        }
        params = json.dumps(params)
        response = json.loads(HTTP_Request(account, endpoint, method, params))


def cancel_order(bot, order_id):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера

    elif bot.service == 'ByBit':
        pass


def amend_order(bot, order_id, data=None):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера

    elif bot.service == 'ByBit':
        pass


def get_position_inform(bot):
    def format_data(service_name, position_list):
        def sort_function(unsorted_list):
            sorted_list = sorted(unsorted_list, key=lambda x: x['side'])
            return sorted_list

        position_inform_list = []
        if service_name == 'Binance':
            position_inform_list = [{
                'symbol': position['symbol'],
                'qty': position['positionAmt'],
                'entryPrice': position['entryPrice'],
                'markPrice': position['markPrice'],
                'unrealisedPnl': position['unRealizedProfit'],
                'side': position['positionSide'],
            } for position in position_list]
        elif service_name == 'ByBit':
            position_inform_list = [{
                'symbol': position['symbol'],
                'qty': position['size'],
                'entryPrice': position['avgPrice'],
                'markPrice': position['markPrice'],
                'unrealisedPnl': position['unrealisedPnl'],
                'side': 'LONG' if position['side'] == 'Buy' else 'SHORT',
            } for position in position_list]
        return sort_function(position_inform_list)

    if bot.account.service.name == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        response = client.futures_position_information(symbol=bot.symbol.name)
        position_inform_list = format_data('Binance', response)
        return position_inform_list

    elif bot.account.service.name == 'ByBit':
        endpoint = "/v5/position/list"
        method = "GET"
        if bot.symbol:
            params = f"category=linear&symbol={bot.symbol.name}"
        else:
            params = f"category=linear&settleCoin=USDT"
        response = json.loads(HTTP_Request(bot.account, endpoint, method, params))
        response = response['result']['list']
        position_inform_list = format_data('ByBit', response)
        return position_inform_list


# def get_current_price(bot, account, category, symbol):
#     if bot.service == 'Binance':
#         client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
#         client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера
#
#     elif bot.service == 'ByBit':
#         pass


def get_position_price(symbol_list):
    # if bot.service == 'Binance':
    #     client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
    #     client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера
    #
    # elif bot.service == 'ByBit':
    pass


def get_qty(bot, symbol_list):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)

    elif bot.service == 'ByBit':
        pass


def get_side(bot, symbol_list):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера

    elif bot.service == 'ByBit':
        pass


# def get_list(bot, account, category='linear', symbol=None, settleCoin='USDT'):
#     if bot.service == 'Binance':
#         client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
#         client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера
#
#     elif bot.service == 'ByBit':
#         pass


def get_order_book(bot, account, category, symbol):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера

    elif bot.service == 'ByBit':
        pass


def get_instruments_info(bot, account, category, symbol=None):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера

    elif bot.service == 'ByBit':
        pass


def get_symbol_set(bot):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера

    elif bot.service == 'ByBit':
        pass


def get_order_status(bot, account, category, symbol, orderLinkId):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера

    elif bot.service == 'ByBit':
        pass


def get_order_created_time(bot, account, category, symbol, orderLinkId):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера

    elif bot.service == 'ByBit':
        pass


def get_order_leaves_qty(bot, account, category, symbol, orderLinkId):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера

    elif bot.service == 'ByBit':
        pass


def get_pnl(bot, account, category, symbol, start_time=0, end_time=0, limit=50):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера

    elif bot.service == 'ByBit':
        pass


# def set_leverage(account, category, symbol, leverage, bot=None):
#     if bot.service == 'Binance':
#         client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
#         client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера
#
#     elif bot.service == 'ByBit':
#         pass


# def get_query_account_coins_balance(account, symbol):
#     if account.service.name == 'Binance':
#         client = Client(account.API_TOKEN, account.SECRET_KEY, testnet=True)
#         response = client.futures_account_balance(symbol=symbol)
#         response = [x for x in response if x['asset'] == 'USDT'][0]
#         return response
#
#     elif account.service.name == 'ByBit':
#         endpoint = "/v5/asset/transfer/query-account-coins-balance"
#         method = "GET"
#         params = f"accountType={account.account_type}&coin=USDT"
#         response = json.loads(HTTP_Request(account, endpoint, method, params))
#         try:
#             return response['result']['balance'][0]
#         except:
#             return None


# def switch_position_mode(bot):
#     if bot.service == 'Binance':
#         client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
#         client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера
#
#     elif bot.service == 'ByBit':
#         pass


def set_trading_stop(bot, positionIdx, takeProfit='0', stopLoss='0', tpSize=None):
    if bot.service == 'Binance':
        client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
        client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера

    elif bot.service == 'ByBit':
        pass


#
# def get_open_orders(bot):
#     if bot.service == 'Binance':
#         client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=True)
#         client.futures_cancel_all_open_orders(symbol=bot.symbol)  # Отменит все ордера
#
#     elif bot.service == 'ByBit':
#         pass


def tg_error_message(bot, response):
    response_data = json.loads(response.text)
    response_data_retcode = str(response_data["retCode"])
    response_data_retmsg = str(response_data["retMsg"])

    if len(response_data_retcode) == 6:
        if response_data_retcode != '110025' and response_data_retcode != '110043':
            tg = TelegramAccount.objects.filter(owner=bot.owner).first()
            if tg:
                chat_id = tg.chat_id
                message = f'Код ошибки: "{response_data_retcode}"\nТекст ошибки: "{response_data_retmsg}"'
                send_telegram_message(chat_id, bot, message)
