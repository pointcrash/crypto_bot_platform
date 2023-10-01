from datetime import datetime

from api_v5 import get_pnl


def calculate_pnl(bot, start_date, end_date):
    pnl = 0
    start_timestamp = datetime.combine(start_date, datetime.min.time()).timestamp() * 1000
    end_timestamp = datetime.combine(end_date, datetime.min.time()).timestamp() * 1000

    start_timestamp = str(int(start_timestamp))
    end_timestamp = str(int(end_timestamp))

    data_list_pnl = get_pnl(bot.account, bot.category, bot.symbol, start_time=start_timestamp, end_time=end_timestamp)
    for data in data_list_pnl:
        pnl += float(data['closedPnl'])

    return round(pnl, 2)
