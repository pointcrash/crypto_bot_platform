from pybit.unified_trading import HTTP


def get_session(account):
    session = HTTP(
        testnet=not account.is_mainnet,
        api_key=account.API_TOKEN,
        api_secret=account.SECRET_KEY,
    )

    return session


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
            "qty": order['quantity'],
        }
        if formatted_order['orderType'] == 'Limit':
            formatted_order['price'] = order['price']
        formatted_order_list.append(formatted_order)

    session = get_session(bot.account)
    response = session.place_batch_order(category=category, request=formatted_order_list)
    return response


if __name__ == "__main__":
    test_session = HTTP(
        testnet=True,
        api_key="WNiu8gV3qoUyjT05WB",
        api_secret="xPNX24SbCF7OJHyUxQxGdb2XOpsnaetIOgrU",
    )

    print(test_session.place_batch_order(
        category="linear",
        request=[
            {
                "category": "linear",
                "symbol": "BTCUSDT",
                "orderType": "Market",
                "side": "Buy",
                "positionIdx": 1,
                "qty": '0.02',
            },
            {
                "category": "linear",
                "symbol": "BTCUSDT",
                "orderType": "Market",
                "side": "Sell",
                "positionIdx": 2,
                "qty": '0.02',
            }
        ]
    ))
