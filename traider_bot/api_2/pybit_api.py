import time
import uuid

from pybit.unified_trading import HTTP

from api_2.formattres import order_formatters


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


def bybit_withdraw(account, symbol, chain, force_chain, address, amount):
    session = get_session(account)

    response = session.withdraw(
        coin=symbol,
        chain=chain,
        address=address,
        amount=amount,
        forceChain=force_chain,
        accountType="FUND",
        timestamp=int(time.time()) * 1000,
    )
    return response


# def create_universal_transfer(
#         account, symbol, amount, from_member_id, to_member_id, from_account_type, to_account_type):
#     session = get_session(account)
#
#     response = session.create_universal_transfer(
#         transferId=str(uuid.uuid4()),
#         coin=symbol,
#         amount=str(amount),
#         fromMemberId=from_member_id,
#         toMemberId=to_member_id,
#         fromAccountType=from_account_type,
#         toAccountType=to_account_type,
#     )
#     return response


if __name__ == "__main__":
    test_session = HTTP(
        testnet=False,
        api_key="xcXVA47NndHFNDBqJ9",
        api_secret="71Xj99PBSljGv8wOer2iRnBt7xF2J6UsF7Ex",
    )

    print(test_session.withdraw(
        coin="USDT",
        chain="TRX",
        address="TLjWZpgjsovzZdH55vvMuMu1gheVSj6nU3",
        amount="5",
        timestamp=int(time.time()) * 1000,
        forceChain=1,
        accountType="FUND",
    ))

    # response = (test_session.get_open_orders(
    #     category="linear",
    #     symbol="ETHUSDT",
    #     openOnly=0,
    # ))
    #
    # for order in response['result']['list']:
    #     print(order_formatters(order))

    # print(test_session.place_batch_order(
    #     category="linear",
    #     request=[
    #         {
    #             "category": "linear",
    #             "symbol": "BTCUSDT",
    #             "orderType": "Market",
    #             "side": "Buy",
    #             "positionIdx": 1,
    #             "qty": '0.02',
    #         },
    #         {
    #             "category": "linear",
    #             "symbol": "BTCUSDT",
    #             "orderType": "Market",
    #             "side": "Sell",
    #             "positionIdx": 2,
    #             "qty": '0.02',
    #         }
    #     ]
    # ))
