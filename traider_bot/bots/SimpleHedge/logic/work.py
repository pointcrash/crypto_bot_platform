import time

from decimal import Decimal

from api_v5 import get_list, get_current_price, set_trading_stop, get_open_orders, cancel_order, switch_position_mode, \
    set_leverage, cancel_all
from bots.bot_logic import logging, get_quantity_from_price
from orders.models import Order
from single_bot.logic.global_variables import lock, global_list_bot_id, global_list_threads
from single_bot.logic.work import append_thread_or_check_duplicate


def work_simple_hedge_bot(bot, smp_hg, first_start=True):
    bot_id = bot.pk
    append_thread_or_check_duplicate(bot_id)
    cancel_all(bot.account, bot.category, bot.symbol)

    # Меняем режим на Хэдж и устанавливаем указанное плечо
    switch_position_mode(bot)
    set_leverage(bot.account, bot.category, bot.symbol, bot.isLeverage, bot)

    bot.bin_order = False
    bot.save()
    psn_add_flag = 0
    round_number = int(bot.symbol.priceScale)
    account = bot.account
    avg_order_links_id = {1: f'{bot.take1}', 2: f'{bot.take2}'}
    symbol_list = get_list(account, symbol=bot.symbol)
    psn_add_flag_2 = False

    try:
        if first_start:
            if float(symbol_list[0]['size']) != 0 or float(symbol_list[1]['size']) != 0:
                logging(bot, 'Ошибка! Есть открытые позиции по выбранной торговой паре.')
                raise Exception(f'Ошибка! Есть открытые позиции по выбранной торговой паре {bot.symbol}.')
    except Exception as e:
        print(f'Error {e}')
        logging(bot, f'Error {e}')
        lock.acquire()
        try:
            if bot_id in global_list_bot_id:
                global_list_bot_id.remove(bot_id)
                del global_list_threads[bot_id]
                bot.is_active = False
                bot.save()
        finally:
            if lock.locked():
                lock.release()
            return None

    current_price = get_current_price(account, bot.category, bot.symbol)
    first_order_qty = get_quantity_from_price(bot.qty, current_price, bot.symbol.minOrderQty, bot.isLeverage)
    tp_size = first_order_qty * Decimal(smp_hg.tpap) / 100

    if first_start or (float(symbol_list[0]['size']) == 0 and float(symbol_list[1]['size']) == 0):
        if bot.price:
            first_order_qty = get_quantity_from_price(bot.qty, bot.price, bot.symbol.minOrderQty, bot.isLeverage)
            trigger_direction = 1 if bot.price > current_price else 2

            for order_side in ['Buy', 'Sell']:
                order = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    side=order_side,
                    orderType="Market",
                    qty=first_order_qty,
                    price=str(bot.price),
                    triggerDirection=trigger_direction,
                    triggerPrice=str(bot.price),
                )
        else:
            for order_side in ['Buy', 'Sell']:
                order = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    side=order_side,
                    orderType="Market",
                    qty=first_order_qty,
                )

            symbol_list = get_list(account, symbol=bot.symbol)

            for position_idx in range(1, 3):
                if position_idx == 1:
                    tp_price = round(
                        Decimal(symbol_list[position_idx - 1]['avgPrice']) * (1 + Decimal(smp_hg.tppp) / 100),
                        round_number)
                else:
                    tp_price = round(
                        Decimal(symbol_list[position_idx - 1]['avgPrice']) * (1 - Decimal(smp_hg.tppp) / 100),
                        round_number)

                set_trading_stop(bot, position_idx, takeProfit=str(tp_price), tpSize=str(tp_size))

    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            if lock.locked():
                lock.release()

            order_clear = True
            time.sleep(5)

            symbol_list = get_list(account, symbol=bot.symbol)
            qty_buy = Decimal(symbol_list[0]['size'])
            qty_sell = Decimal(symbol_list[1]['size'])

            if qty_buy != 0 and qty_sell != 0:
                psn_add_flag_2 = False
                for position_idx, current_qty in [(1, qty_buy), (2, qty_sell)]:
                    entry_price = Decimal(symbol_list[position_idx - 1]['avgPrice'])
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
                            if position_idx == 1:
                                bot.take1 = order.orderLinkId
                            else:
                                bot.take2 = order.orderLinkId
                            bot.save()

                    elif current_qty > first_order_qty:
                        avg_order_links_id[position_idx] = ''
                        if position_idx == 1:
                            bot.take1 = ''
                        else:
                            bot.take2 = ''
                        bot.save()

                        if bot.bin_order:
                            psn_add_flag = 0

                        if psn_add_flag < 2:
                            order_list = get_open_orders(bot=bot)
                            if order_list and order_clear:
                                for order in order_list:
                                    order_id = order['orderId']
                                    cancel_order(bot, order_id)
                                    order_clear = False

                            position_idx_avg = position_idx
                            tp_sl_size = abs(first_order_qty - Decimal(symbol_list[position_idx_avg - 1]['size']))
                            tp_sl_response = set_trading_stop(bot, position_idx_avg, takeProfit=str(entry_price), tpSize=str(tp_sl_size))
                            if tp_sl_response['retMsg'] != 'OK':
                                tp_sl_response = set_trading_stop(bot, position_idx_avg, stopLoss=str(entry_price),
                                                                  tpSize=str(tp_sl_size))
                            if tp_sl_response['retMsg'] != 'OK':
                                raise Exception('Ошибка размещения ордеров закрытия лишней маржи')

                        psn_add_flag += 1
                        psn_add_flag_2 = True

                    else:
                        psn_add_flag = 0
                        avg_order_links_id[position_idx] = ''
                        if position_idx == 1:
                            bot.take1 = ''
                        else:
                            bot.take2 = ''
                        bot.save()

                        order_list = get_open_orders(bot=bot)
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
                # raise Exception('Нулевая позиция')
                pass

            order_clear = True
            if psn_add_flag_2:
                bot.bin_order = False
            lock.acquire()

    except Exception as e:
        print(f'Error {e}')
        logging(bot, f'Error {e}')
        lock.acquire()
        try:
            if bot_id in global_list_bot_id:
                global_list_bot_id.remove(bot_id)
                del global_list_threads[bot_id]
                bot.is_active = False
                bot.save()
        finally:
            if lock.locked():
                lock.release()
    finally:
        if lock.locked():
            lock.release()
