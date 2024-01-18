import json
from decimal import Decimal

from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message


def cancel_all(account, category, symbol):
    return response


def cancel_order(bot, order_id):
    return response


def amend_order(bot, order_id, data=None):
    return response


def get_current_price(account, category, symbol):
    try:
        return Decimal(response["result"]["list"][0]["lastPrice"])
    except:
        return None
        # raise Exception('Ошибка запроса текущей цены "get_current_price"')


def get_position_price(symbol_list):
    if len(symbol_list) == 1:
        return Decimal(symbol_list[0]["avgPrice"])
    else:
        return [Decimal(i['avgPrice']) for i in symbol_list]


def get_qty(symbol_list):
    if len(symbol_list) == 1:
        return Decimal(symbol_list[0]["size"])
    else:
        return [Decimal(qty['size']) for qty in symbol_list]


def get_side(symbol_list):
    if len(symbol_list) == 1:
        return symbol_list[0]["side"]
    else:
        return [i['side'] for i in symbol_list]


def get_list(account, category='linear', symbol=None, settleCoin='USDT'):
    return response['result']['list']


def get_order_book(account, category, symbol):
    return response


def get_instruments_info(account, category, symbol=None):
    return response


def get_symbol_set():
    return symbol_set


def get_order_status(account, category, symbol, orderLinkId):
    return response['result']['list'][0]['orderStatus']


def get_order_created_time(account, category, symbol, orderLinkId):
    return response['result']['list'][0]['createdTime']


def get_order_leaves_qty(account, category, symbol, orderLinkId):
    return response['result']['list'][0]['leavesQty']


def get_pnl(account, category, symbol, start_time=0, end_time=0, limit=50):
    return response['result']['list']


def set_leverage(account, category, symbol, leverage, bot=None):
    pass


def get_query_account_coins_balance(account):
    return response['result']['balance']


def switch_position_mode(bot):
    pass


def set_trading_stop(bot, positionIdx, takeProfit='0', stopLoss='0', tpSize=None):
    return response


def get_open_orders(bot):
    return 'OK', response['result']['list']


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
