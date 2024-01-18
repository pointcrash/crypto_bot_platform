from datetime import datetime

from api.api_v5 import get_pnl


def calculate_pnl(bot, start_date, end_date):
    try:
        pnl = 0
        pnl_buy = 0
        pnl_sell = 0
        # start_timestamp = datetime.combine(start_date, datetime.min.time()).timestamp() * 1000
        # end_timestamp = datetime.combine(end_date, datetime.min.time()).timestamp() * 1000

        start_timestamp = start_date.timestamp()
        end_timestamp = end_date.timestamp()
        start_timestamp = str(int(start_timestamp) * 1000)
        end_timestamp = str(int(end_timestamp) * 1000)

        data_list_pnl = get_pnl(bot.account, bot.category, bot.symbol, start_time=start_timestamp, end_time=end_timestamp)
        for data in data_list_pnl:
            pnl += float(data['closedPnl'])
            if data['side'] == 'Sell':
                pnl_buy += float(data['closedPnl'])
            elif data['side'] == 'Buy':
                pnl_sell += float(data['closedPnl'])

        return {'pnl': round(pnl, 2), 'pnl_buy': round(pnl_buy, 2), 'pnl_sell': round(pnl_sell, 2)}
    except Exception as e:
        print(e)
        return None
