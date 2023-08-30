from bots.models import Bot


def create_set0osn_bot_obj(user, account, symbol, psn, count_dict):
    side = 'Buy' if psn['side'] == 'Sell' else 'Sell'
    bot = Bot.objects.create(
        owner=user,
        account=account,
        category='inverse',
        symbol=symbol,
        isLeverage=int(psn['leverage']),
        side=side,
        orderType='Market',
        qty=count_dict['margin'],
        time_sleep=5,
        work_model='set0psn',
    )

    return bot
