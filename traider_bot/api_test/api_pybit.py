import time
from datetime import datetime, timedelta

from pybit.unified_trading import HTTP


main_api_key = 'Rwt3UiqjKvIXe39h1W'
main_api_secret = 'kyzgLKPSWlYzQUbJtX51tWkyiuYW3IQHXgO3'


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
    # response = session.get_wallet_balance(accountType="UNIFIED", currency='USDT')
    return response


def bybit_get_pnl_by_time(start_time, end_time):
    session = get_session()
    start_time = int(start_time.timestamp() * 1000)
    end_time = int(end_time.timestamp() * 1000)
    total_pnl = 0

    response = session.get_closed_pnl(
        category="linear",
        symbol='1000BONKUSDT',
        startTime=start_time,
        endTime=end_time,
    )

    for trade in response['result']['list']:
        total_pnl += float(trade['closedPnl'])

    return total_pnl


def get_dates_in_ms(days_back=30, interval_days=7):
    dates_in_ms = []
    current_date = datetime.now()

    for days_ago in range(0, days_back + 1, interval_days):
        date = current_date - timedelta(days=days_ago)
        date_in_ms = int(time.mktime(date.timetuple()) * 1000)
        dates_in_ms.append(date_in_ms)

    return dates_in_ms


if __name__ == '__main__':
    def get_pnl_by_time_copy_without_bot(service_name, start_time, end_time=None):
        get_pnl_func = None

        #  Get 'get_pnl_func'
        if service_name == 'Binance':
            # get_pnl_func = binance_get_pnl_by_time
            get_pnl_func = None
        elif service_name == 'ByBit':
            get_pnl_func = bybit_get_pnl_by_time

        #  Calculate sum total pnl by time
        if get_pnl_func is not None:
            total_pnl = 0
            if end_time is None:
                end_time = datetime.now()

            while end_time - start_time > timedelta(days=7):
                seven_days_later = start_time + timedelta(days=7)
                pnl = get_pnl_func(start_time, seven_days_later)
                total_pnl += pnl
                start_time = seven_days_later

            if end_time - start_time < timedelta(days=7):
                pnl = get_pnl_func(start_time, end_time)
                total_pnl += pnl

            return total_pnl


    print(get_pnl_by_time_copy_without_bot('ByBit', start_time=datetime.now() - timedelta(days=29)))

    # start_time = datetime.now() - timedelta(days=7)
    # end_time = datetime.now()
    #
    # x = bybit_get_pnl_by_time(start_time, end_time)
    # print(x)
    # for i in x['result']['list']:
    #     print(i)
    # print(bybit_test())
