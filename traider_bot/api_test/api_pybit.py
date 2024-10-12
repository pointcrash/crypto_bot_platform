import time
from datetime import datetime, timedelta

from pybit.unified_trading import HTTP


main_api_key = 'ILF3a7JQfa1ugTCsf5'
main_api_secret = '3TkLM6WYDyokVJyywzF130E1OULHAGTooqpU'


def get_session():
    session = HTTP(
        testnet=False,
        api_key=main_api_key,
        api_secret=main_api_secret,
    )

    return session


def bybit_set_trading_stop():
    session = get_session()
    response = session.get_wallet_balance(
        accountType='UNIFIED',
        coin='USDT'
    )
    return response


def bybit_set_margin_mode():
    session = get_session()
    response = session.set_margin_mode(
        setMarginMode='REGULAR_MARGIN',
    )
    return response


def bybit_get_position_info():
    session = get_session()
    response = session.get_positions(category='linear', settleCoin='USDT')
    return response


def bybit_test():
    session = get_session()
    response = session.get_transaction_log(accountType="UNIFIED", currency='USDT')
    return response


def get_dates_in_ms(days_back=30, interval_days=7):
    dates_in_ms = []
    current_date = datetime.now()

    for days_ago in range(0, days_back + 1, interval_days):
        date = current_date - timedelta(days=days_ago)
        date_in_ms = int(time.mktime(date.timetuple()) * 1000)
        dates_in_ms.append(date_in_ms)

    return dates_in_ms


if __name__ == '__main__':
    # dates = get_dates_in_ms(30, 7)
    # for date in dates:
    #     print(date)
    x = bybit_test()
    for i in x['result']['list']:
        print(i)
    # print(bybit_test())
