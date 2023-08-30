from decimal import Decimal

from api_v5 import get_list, set_trading_stop, cancel_all
from orders.models import Order


def stopping_set_zero_psn_bot(bot, account, symbol):
    qty, side, position_idx = None, None, None
    positions = get_list(account, symbol=symbol)
    for psn in positions:
        if Decimal(psn['unrealisedPnl']) > -1:
            position_idx = psn['positionIdx']
            side = 'Buy' if psn['side'] == 'Sell' else 'Sell'
            qty = psn['size']
            break

    # Отмена всех ордеров
    cancel_all(bot.account, bot.category, bot.symbol)

    # Закрытие плюсовой позиции
    if side and position_idx:
        drop_order = Order.objects.create(
            bot=bot,
            category=bot.category,
            symbol=symbol.name,
            side=side,
            orderType='Market',
            qty=qty,
            positionIdx=position_idx,
        )

    # Инвертируем позицию и снимаем стоп лосс с минусовой позиции
    print('position_idx------------', position_idx)
    position_idx = '1' if position_idx == '2' else '2'
    set_trading_stop(bot, position_idx)
