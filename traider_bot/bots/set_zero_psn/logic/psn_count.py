from decimal import Decimal


def psn_count(psn, price_scale, tick_size, trend_number=None, additional_losses=0):
    pnl = psn['unrealisedPnl']
    tick_size = Decimal(tick_size)
    trend_number = 1 if not trend_number else int(trend_number)
    if '-' in pnl:
        count_dict = dict()
        side = psn['side']
        mark_price = Decimal(psn['markPrice'])
        entry_price = Decimal(psn['avgPrice'])
        leverage = Decimal(psn['leverage'])
        qty = Decimal(psn['size'])

        if side == 'Buy':
            mark_price += tick_size
            for trend in range(trend_number, 4):
                stop_price = round(mark_price - (mark_price * trend / 100), price_scale)
                pnl_old = round((stop_price - entry_price) * qty, 2) + additional_losses
                pnl_new = -pnl_old
                margin = round(pnl_new * mark_price / (leverage * (mark_price - stop_price)), 2)

                count_dict[str(trend)] = {
                    'stop_price': stop_price,
                    'pnl_old': pnl_old,
                    'pnl_new': pnl_new,
                    'margin': margin,
                }

        elif side == 'Sell':
            mark_price -= tick_size
            for trend in range(trend_number, 4):
                stop_price = round(mark_price + (mark_price * trend / 100), price_scale)
                pnl_old = round((entry_price - stop_price) * qty, 2) + additional_losses
                pnl_new = -pnl_old
                margin = round(pnl_new * mark_price / (leverage * (stop_price - mark_price)), 2)

                count_dict[str(trend)] = {
                    'stop_price': stop_price,
                    'pnl_old': pnl_old,
                    'pnl_new': pnl_new,
                    'margin': margin,
                }
        return count_dict
    else:
        return None


def calculate_loss():
    pass