from orders.models import Order
from api_v5 import *


def bot_work_start():
    while True:
        BTC_qty = get_qty_BTC()
        if not BTC_qty:
            print(('The cycle is over'))
            break
        else:
            current_price = get_price_BTC()
            average_price = get_position_price_BTC()
