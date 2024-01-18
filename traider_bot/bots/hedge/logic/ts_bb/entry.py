from api.api_v5 import get_current_price, switch_position_mode, set_leverage, get_qty
from bots.bot_logic import get_quantity_from_price, func_get_symbol_list
from bots.hedge.logic.ts_bb.work import work_ts_bb_bot
from orders.models import Order
from single_bot.logic.work import append_thread_or_check_duplicate


def entry_ts_bb_bot(bot):
    bot_id = bot.pk
    append_thread_or_check_duplicate(bot_id, is_ts_bot=False)
    switch_position_mode(bot)
    set_leverage(bot.account, bot.category, bot.symbol, bot.isLeverage)
    current_price = get_current_price(bot.account, bot.category, bot.symbol)

    symbol_list = func_get_symbol_list(bot)

    if all(get_qty(symbol_list)[position_idx] for position_idx in [0, 1]):
        work_ts_bb_bot(bot)

    else:
        for side in ['Buy', 'Sell']:
            order = Order.objects.create(
                bot=bot,
                category=bot.category,
                symbol=bot.symbol.name,
                side=side,
                orderType='Market',
                qty=get_quantity_from_price(bot.qty, current_price, bot.symbol.minOrderQty, bot.isLeverage),
            )
        work_ts_bb_bot(bot)
