import time
from decimal import Decimal
from api_v5 import get_list, get_current_price, set_trading_stop, get_pnl
from bots.bot_logic import get_quantity_from_price, logging
from bots.set_zero_psn.logic.psn_count import psn_count
from single_bot.logic.global_variables import lock, global_list_bot_id

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from orders.models import Order


def work_set0psn_bot_by_market(bot, mark_price, count_dict, trend):
    bot_id = bot.pk
    entry_price = mark_price
    bot_id_append_global_list(bot_id)
    order_side = bot.side
    leverage = bot.isLeverage
    price_scale = int(bot.symbol.priceScale)
    leverage_trend = Decimal(str(trend / leverage / 100))
    qty = get_quantity_from_price(count_dict['margin'], mark_price, bot.symbol.minOrderQty, bot.isLeverage)
    position_idx_plus = 1 if order_side == 'Buy' else 2
    position_idx_minus = 2 if order_side == 'Buy' else 1
    tick_size = Decimal(bot.symbol.tickSize)
    order_stop_loss = 0
    sl_check = False
    max_order_qty = Decimal(bot.symbol.maxOrderQty)

    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            if lock.locked():
                lock.release()

            # Запрашиваем список открытых позиций по торговой паре
            positions_list = get_list(bot.account, symbol=bot.symbol)
            by_psn_qty = Decimal(positions_list[0]['size'])
            sell_psn_qty = Decimal(positions_list[1]['size'])

            # Действия в зависимости от наличия открытых позиций
            if not by_psn_qty and not sell_psn_qty:
                logging(bot,
                        f'Обе позиции закрыты. Завершение работы...')
                bot_id_remove_global_list(bot)
                break

            elif by_psn_qty and sell_psn_qty:
                # Выставляем stopLoss для минусовой позиции
                set_trading_stop(bot, position_idx_minus, stopLoss=str(count_dict['stop_price']))

                current_price = get_current_price(bot.account, bot.category, bot.symbol)

                if current_price:
                    if order_side == 'Buy':
                        plus_psn_stop_loss = round(current_price - (current_price * leverage_trend), price_scale)
                        reduce_sl = True if plus_psn_stop_loss > order_stop_loss else False
                    else:
                        plus_psn_stop_loss = round(current_price + (current_price * leverage_trend), price_scale)
                        reduce_sl = True if plus_psn_stop_loss < order_stop_loss else False

                    if reduce_sl:
                        set_trading_stop(bot, position_idx_plus, takeProfit=str(count_dict['stop_price']),
                                         stopLoss=str(plus_psn_stop_loss))
                        logging(bot, f'Переставили SL+, new={str(plus_psn_stop_loss)}, old={str(order_stop_loss)}')
                        order_stop_loss = plus_psn_stop_loss
                time.sleep(bot.time_sleep)
                continue

            else:
                set_trading_stop(bot, position_idx_minus)

                if sl_check:
                    while True:
                        current_price = get_current_price(bot.account, bot.category, bot.symbol)
                        if not current_price:
                            time.sleep(5)
                            continue
                        if (order_side == 'Buy' and current_price > entry_price) or (order_side == 'Sell' and current_price < entry_price):
                            time.sleep(15)
                            continue
                        break

                    time.sleep(15)
                    losses_pnl = Decimal(get_pnl(bot.account, bot.category, bot.symbol.name, limit=1)[0]['closedPnl'])
                    logging(bot, f'LOSSES_PNL = {losses_pnl}')
                    additional_losses = 0 if losses_pnl > 0 else losses_pnl

                    symbol_list = get_list(bot.account, symbol=bot.symbol)
                    psn = symbol_list[0] if float(symbol_list[0]['size']) != 0 else symbol_list[1]
                    count_dict = psn_count(psn, price_scale, tick_size, trend, additional_losses)[str(trend)]
                    mark_price = Decimal(psn['markPrice'])
                    qty = get_quantity_from_price(count_dict['margin'], mark_price, bot.symbol.minOrderQty,
                                                  bot.isLeverage)
                    logging(bot, f'Новые данные qty={qty}, margin={count_dict["margin"]}')

                sl_check = True
                if order_side == 'Buy':
                    order_stop_loss = round(mark_price - (mark_price * leverage_trend), price_scale)
                else:
                    order_stop_loss = round(mark_price + (mark_price * leverage_trend), price_scale)

                if qty >= max_order_qty:
                    half_qty = qty / 2
                    for _ in range(2):
                        order = Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            side=order_side,
                            orderType="Market",
                            qty=half_qty,
                            takeProfit=str(count_dict['stop_price']),
                            stopLoss=str(order_stop_loss),
                        )
                else:
                    order = Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side=order_side,
                        orderType="Market",
                        qty=qty,
                        takeProfit=str(count_dict['stop_price']),
                        stopLoss=str(order_stop_loss),
                    )

            lock.acquire()
    finally:
        if lock.locked():
            lock.release()


def bot_id_remove_global_list(bot):
    lock.acquire()
    global_list_bot_id.remove(bot.pk)
    if lock.locked():
        lock.release()
    bot.is_active = False
    bot.save()


def bot_id_append_global_list(bot_id):
    lock.acquire()
    try:
        if bot_id not in global_list_bot_id:
            global_list_bot_id.add(bot_id)
    finally:
        if lock.locked():
            lock.release()
