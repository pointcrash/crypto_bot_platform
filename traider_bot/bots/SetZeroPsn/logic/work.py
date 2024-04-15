import time

from decimal import Decimal
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()
from api.api_v5_bybit import get_list, get_current_price, set_trading_stop, get_order_status
from bots.bot_logic import get_quantity_from_price, logging
from bots.models import Log, Bot
from bots.SetZeroPsn.logic.psn_count import psn_count
from orders.models import Order
from single_bot.logic.global_variables import lock, global_list_bot_id
from single_bot.logic.work import append_thread_or_check_duplicate


def work_set_zero_psn_bot(bot, mark_price, count_dict, trend):
    bot_id = bot.pk
    qty = get_quantity_from_price(count_dict['margin'], mark_price, bot.symbol.minOrderQty, bot.isLeverage)
    append_thread_or_check_duplicate(bot_id)
    orderLinkId = None
    order_status = None
    order_stop_loss = 0
    leverage = bot.isLeverage
    price_scale = int(bot.symbol.priceScale)
    leverage_trend = Decimal(str(trend / leverage / 100))
    order_side = bot.side
    tick_size = Decimal(bot.symbol.tickSize)
    we_have_2psn_flag = False
    psn_loss_flag = False

    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            if lock.locked():
                lock.release()

            # Запрашиваем список открытых позиций по торговой паре
            positions_list = get_list(bot.account, symbol=bot.symbol)
            by_psn_qty = Decimal(positions_list[0]['size'])
            sell_psn_qty = Decimal(positions_list[1]['size'])

            if orderLinkId:
                order_status = get_order_status(bot.account, bot.category, bot.symbol, orderLinkId)

            # Действия в зависимости от наличия открытых позиций
            if not by_psn_qty and not sell_psn_qty:
                logging(bot,
                        f'Обе позиции закрыты. Завершение работы...')
                if_not_psn_actions(bot)
                break
            elif (by_psn_qty and sell_psn_qty) or order_status == 'Order not found' or order_status == 'New':
                # Инвертируем индекс позиции в зависимости от направления выставления плюсового ордера
                position_idx = 2 if order_side == 'Buy' else 1
                # Выставляем stopLoss для минусовой позиции
                set_trading_stop(bot, position_idx)

                if order_status == 'New':
                    last_log = Log.objects.filter(bot=bot).last()
                    f_line = f'Ордер id={orderLinkId} успешно выставлен qty={qty}, price={mark_price}, SL={str(order_stop_loss)}'
                    if f_line not in last_log.content:
                        logging(bot, f_line)

                if order_status == 'Order not found' and not (by_psn_qty and sell_psn_qty):
                    logging(bot, f'Ордер id={orderLinkId} не найден qty={qty}, price={mark_price}, SL={str(order_stop_loss)}')

                    recalc = False
                    current_price = get_current_price(bot.account, bot.category, bot.symbol)
                    if current_price:
                        if order_side == 'Sell':
                            current_price = current_price + tick_size
                            recalc = True if current_price > mark_price + (tick_size * 5) else False
                        elif order_side == 'Buy':
                            current_price = current_price - tick_size
                            recalc = True if current_price < mark_price - (tick_size * 5) else False

                    if recalc or we_have_2psn_flag:
                        if recalc:
                            logging(bot, f'recalc')
                        if we_have_2psn_flag:
                            logging(bot, f'we_have_2psn_flag')
                        additional_losses = 0

                        if we_have_2psn_flag:
                            if order_side == 'Buy':
                                additional_losses = round((order_stop_loss - mark_price) * qty, 2)
                                logging(bot, f'Считаем доп потери {additional_losses}')
                            else:
                                additional_losses = round((mark_price - order_stop_loss) * qty, 2)
                                logging(bot, f'Считаем доп потери {additional_losses}')
                            we_have_2psn_flag = False

                        symbol_list = get_list(bot.account, symbol=bot.symbol)
                        psn = symbol_list[0] if float(symbol_list[0]['size']) != 0 else symbol_list[1]
                        count_dict = psn_count(psn, price_scale, tick_size, trend, additional_losses)[str(trend)]
                        mark_price = Decimal(psn['markPrice'])
                        qty = get_quantity_from_price(count_dict['margin'], mark_price, bot.symbol.minOrderQty,
                                                      bot.isLeverage)
                        logging(bot, f'Новые данные qty={qty}, entry_price={mark_price}, margin={count_dict["margin"]}')

                    orderLinkId = None
                    order_status = None

                if by_psn_qty and sell_psn_qty:
                    we_have_2psn_flag = True

                    # Инвертируем индекс позиции в зависимости от направления выставления плюсового ордера
                    position_idx = 2 if order_side == 'Buy' else 1
                    # Выставляем stopLoss для минусовой позиции
                    set_trading_stop(bot, position_idx, stopLoss=str(count_dict['stop_price']))

                    position_idx = 1 if order_side == 'Buy' else 2
                    current_price = get_current_price(bot.account, bot.category, bot.symbol)

                    if current_price:
                        if order_side == 'Buy':
                            plus_psn_stop_loss = round(current_price - (current_price * leverage_trend), price_scale)
                            reduce_sl = True if plus_psn_stop_loss > order_stop_loss else False
                        else:
                            plus_psn_stop_loss = round(current_price + (current_price * leverage_trend), price_scale)
                            reduce_sl = True if plus_psn_stop_loss < order_stop_loss else False

                        if reduce_sl:
                            set_trading_stop(bot, position_idx, takeProfit=str(count_dict['stop_price']),
                                             stopLoss=str(plus_psn_stop_loss))
                            logging(bot, f'Переставили SL, new={str(plus_psn_stop_loss)}, old={str(order_stop_loss)}')
                            order_stop_loss = plus_psn_stop_loss
                time.sleep(bot.time_sleep)
                continue

            else:
                if order_side == 'Buy':
                    mark_price += tick_size
                    order_stop_loss = round(mark_price - (mark_price * leverage_trend), price_scale)
                else:
                    mark_price -= tick_size
                    order_stop_loss = round(mark_price + (mark_price * leverage_trend), price_scale)

                order = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    side=order_side,
                    orderType="Limit",
                    qty=qty,
                    price=mark_price,
                    takeProfit=str(count_dict['stop_price']),
                    stopLoss=str(order_stop_loss),
                )

                logging(bot, f'Отправлен ордер qty={qty}, price={mark_price}, SL={str(order_stop_loss)}')

                orderLinkId = order.orderLinkId

                # # Инвертируем индекс позиции в зависимости от направления выставления плюсового ордера
                # position_idx = 2 if order_side == 'Buy' else 1
                # # Выставляем stopLoss для минусовой позиции
                # set_trading_stop(bot, position_idx, stopLoss=str(count_dict['stop_price']))

            lock.acquire()

    finally:
        if lock.locked():
            lock.release()


def if_not_psn_actions(bot):
    lock.acquire()
    global_list_bot_id.remove(bot.pk)
    if lock.locked():
        lock.release()
    bot.is_active = False
    bot.save()