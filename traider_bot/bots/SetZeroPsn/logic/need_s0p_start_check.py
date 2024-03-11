from decimal import Decimal
from api.api_v5_bybit import get_list, cancel_all
from bots.bot_logic import logging
from bots.SetZeroPsn.logic.psn_count import psn_count
from bots.SetZeroPsn.logic.work_by_market import work_set0psn_bot_by_market, bot_id_remove_global_list


def need_set0psn_start_check(bot, psn):
    symbol = bot.symbol
    trend = bot.set0psn.trend
    # symbol_list = get_list(bot.account, symbol=symbol)
    # psn = symbol_list[0] if float(symbol_list[0]['size']) != 0 else symbol_list[1]
    losses_pnl = Decimal(psn['unrealisedPnl'])
    limit_losses_pnl = Decimal(bot.set0psn.limit_pnl)
    max_margin = bot.set0psn.max_margin

    if losses_pnl <= limit_losses_pnl:
        count_dict = psn_count(psn, int(symbol.priceScale), symbol.tickSize, trend_number=trend)[str(trend)]
        if max_margin:
            if count_dict['margin'] < Decimal(max_margin):
                transition_to_set0psn(bot, psn, count_dict)
                return True

            else:
                cancel_all(bot.account, bot.category, bot.symbol)
                logging(bot,
                        f'Not enough margin for switch mod to "set0psn". Need margin: {count_dict["margin"]}, your Margin Limit: {max_margin}')
                bot_id_remove_global_list(bot)
                return True

        else:
            transition_to_set0psn(bot, psn, count_dict)
            return True


def transition_to_set0psn(bot, psn, count_dict):
    cancel_all(bot.account, bot.category, bot.symbol)

    side = 'Buy' if psn['side'] == 'Sell' else 'Sell'
    bot.side = side
    bot.time_sleep = 15
    bot.work_model = 'set0psn'
    bot.save()

    work_set0psn_bot_by_market(bot, Decimal(psn['markPrice']), count_dict, int(bot.set0psn.trend))
