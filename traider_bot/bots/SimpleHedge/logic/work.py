import time

from decimal import Decimal

from api_v5 import get_list, get_current_price, set_trading_stop, get_open_orders, cancel_order
from bots.bot_logic import logging, get_quantity_from_price
from orders.models import Order
from single_bot.logic.global_variables import lock, global_list_bot_id
from single_bot.logic.work import append_thread_or_check_duplicate


def work_simple_hedge_bot(bot, smp_hg):
    bot_id = bot.pk
    psn_add_flag = False
    round_number = int(bot.symbol.priceScale)
    account = bot.account
    avg_order_links_id = {1: '', 2: ''}
    symbol_list = get_list(account, symbol=bot.symbol)
    if float(symbol_list[0]['size']) != 0 or float(symbol_list[1]['size']) != 0:
        logging(bot, 'Ошибка! Есть открытые позиции по выбранной торговой паре.')
        return None

    append_thread_or_check_duplicate(bot_id)
    current_price = get_current_price(account, bot.category, bot.symbol)
    entry_price = current_price
    first_order_qty = get_quantity_from_price(bot.qty, current_price, bot.symbol.minOrderQty, bot.isLeverage)

    for order_side in ['Buy', 'Sell']:
        order = Order.objects.create(
            bot=bot,
            category=bot.category,
            symbol=bot.symbol.name,
            side=order_side,
            orderType="Market",
            qty=first_order_qty,
        )

    tp_size = first_order_qty * Decimal(smp_hg.tpap) / 100
    for position_idx in range(1, 3):
        if position_idx == 1:
            tp_price = round(current_price * (1 + Decimal(smp_hg.tppp) / 100), round_number)
        else:
            tp_price = round(current_price * (1 - Decimal(smp_hg.tppp) / 100), round_number)

        set_trading_stop(bot, position_idx, takeProfit=str(tp_price), tpSize=str(tp_size))

    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            if lock.locked():
                lock.release()

            time.sleep(10)

            symbol_list = get_list(account, symbol=bot.symbol)
            qty_buy = Decimal(symbol_list[0]['size'])
            qty_sell = Decimal(symbol_list[1]['size'])
            if qty_buy != 0 and qty_sell != 0:
                for position_idx, current_qty in [(1, qty_buy), (2, qty_sell)]:
                    if current_qty < first_order_qty:
                        if not avg_order_links_id[position_idx]:
                            side = 'Buy' if position_idx == 1 else 'Sell'
                            price = str(round(Decimal(symbol_list[0]['avgPrice']), round_number))
                            avg_qty = first_order_qty - current_qty
                            order = Order.objects.create(
                                bot=bot,
                                category=bot.category,
                                symbol=bot.symbol.name,
                                side=side,
                                orderType="Limit",
                                qty=avg_qty,
                                price=price,
                            )
                            avg_order_links_id[position_idx] = order.orderLinkId

                    elif current_qty > first_order_qty:
                        avg_order_links_id[position_idx] = ''
                        psn_add_flag = True

                        order_list = get_open_orders(bot=bot)
                        if order_list:
                            for order in order_list:
                                order_id = order['orderId']
                                cancel_order(bot, order_id)
                                time.sleep(1)

                        position_idx_avg = position_idx
                        if position_idx_avg == 1:
                            tp_sl_size = abs(first_order_qty - Decimal(symbol_list[0]['size']))
                            if Decimal(symbol_list[0]['avgPrice']) < entry_price:
                                set_trading_stop(bot, position_idx_avg, takeProfit=str(entry_price), tpSize=str(tp_sl_size))
                            else:
                                set_trading_stop(bot, position_idx_avg, stopLoss=str(entry_price), tpSize=str(tp_sl_size))

                        else:
                            tp_sl_size = abs(first_order_qty - Decimal(symbol_list[1]['size']))
                            if Decimal(symbol_list[1]['avgPrice']) > entry_price:
                                set_trading_stop(bot, position_idx_avg, takeProfit=str(entry_price), tpSize=str(tp_sl_size))
                            else:
                                set_trading_stop(bot, position_idx_avg, stopLoss=str(entry_price), tpSize=str(tp_sl_size))

                    else:
                        avg_order_links_id[position_idx] = ''
                        order_list = get_open_orders(bot=bot)
                        # print(order_list)
                        # if order_list:
                        #     for order in order_list:
                        #         order_id = order['orderId']
                        #         print(order_id)
                        #         print(cancel_order(bot, order_id))
                        #         time.sleep(1)
                        tp_order_side = 'Sell' if position_idx == 1 else 'Buy'

                        if not order_list:
                            if position_idx == 1:
                                tp_price = round(Decimal(symbol_list[0]['avgPrice']) * (1 + Decimal(smp_hg.tppp) / 100), round_number)
                            else:
                                tp_price = round(Decimal(symbol_list[1]['avgPrice']) * (1 - Decimal(smp_hg.tppp) / 100), round_number)

                            set_trading_stop(bot, position_idx, takeProfit=str(tp_price), tpSize=str(tp_size))

                        elif tp_order_side not in [sd['side'] for sd in order_list]:
                            if position_idx == 1:
                                tp_price = round(Decimal(symbol_list[0]['avgPrice']) * (1 + Decimal(smp_hg.tppp) / 100), round_number)
                            else:
                                tp_price = round(Decimal(symbol_list[1]['avgPrice']) * (1 - Decimal(smp_hg.tppp) / 100), round_number)

                            set_trading_stop(bot, position_idx, takeProfit=str(tp_price), tpSize=str(tp_size))

            else:
                raise 'Нулевая позиция'

            lock.acquire()
    finally:
        if lock.locked():
            lock.release()
            