from decimal import Decimal


def psn_count(psn):
    pnl = psn['unrealisedPnl']
    if '-' in pnl:
        count_dict = dict()
        side = psn['side']
        mark_price = Decimal(psn['markPrice'])
        entry_price = Decimal(psn['avgPrice'])
        leverage = Decimal(psn['leverage'])
        qty = Decimal(psn['size'])

        if side == 'Buy':
            for trend in range(1, 4):
                stop_price = mark_price - (mark_price * trend / 100)
                pnl_old = (stop_price - entry_price) * qty
                pnl_new = -pnl_old
                margin = pnl_new * mark_price / (leverage * (mark_price - stop_price))

                count_dict[str(trend)] = {
                    'stop_price': stop_price,
                    'pnl_old': pnl_old,
                    'pnl_new': pnl_new,
                    'margin': margin,
                }

        elif side == 'Sell':
            for trend in range(1, 4):
                stop_price = mark_price + (mark_price * trend / 100)
                pnl_old = (entry_price - stop_price) * qty
                pnl_new = -pnl_old
                margin = pnl_new * mark_price / (leverage * (stop_price - mark_price))

                count_dict[str(trend)] = {
                    'stop_price': stop_price,
                    'pnl_old': pnl_old,
                    'pnl_new': pnl_new,
                    'margin': margin,
                }
        return count_dict
    else:
        return None

