from pybit.unified_trading import HTTP


main_api_key = 'xcXVA47NndHFNDBqJ9'
main_api_secret = '71Xj99PBSljGv8wOer2iRnBt7xF2J6UsF7Ex'


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


if __name__ == '__main__':
    pass
    # print(bybit_set_margin_mode())
