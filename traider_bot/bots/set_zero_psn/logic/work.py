import time

from decimal import Decimal

from api_v5 import get_list, get_current_price, set_trading_stop, get_order_status
from bots.bot_logic import get_quantity_from_price
from bots.set_zero_psn.logic.psn_count import psn_count
from orders.models import Order
from single_bot.logic.global_variables import lock, global_list_bot_id
from single_bot.logic.work import append_thread_or_check_duplicate


def work_set_zero_psn_bot(bot, mark_price, count_dict, trend):
    bot_id = bot.pk
    append_thread_or_check_duplicate(bot_id)
    orderLinkId = None
    order_status = None
    order_stop_loss = 0
    leverage = bot.isLeverage
    price_scale = int(bot.symbol.priceScale)
    leverage_trend = Decimal(str(trend / leverage / 100))
    order_side = bot.side
    tick_size = Decimal(bot.symbol.tickSize)

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
                if_not_psn_actions(bot)
                break
            elif (by_psn_qty and sell_psn_qty) or order_status == 'Order not found' or order_status == 'New':
                if order_status == 'Order not found':
                    current_price = get_current_price(bot.account, bot.category, bot.symbol)
                    if current_price:
                        if order_side == 'Sell':
                            current_price = current_price + tick_size
                            if current_price > mark_price + (tick_size * 5):
                                mark_price = current_price
                        else:
                            current_price = current_price - tick_size
                            if current_price < mark_price - (tick_size * 5):
                                mark_price = current_price
                    symbol_list = get_list(bot.account, symbol=bot.symbol)
                    psn = symbol_list[0] if float(symbol_list[0]['size']) != 0 else symbol_list[1]
                    count_dict = psn_count(psn, price_scale, tick_size, mark_price, trend)[str(trend)]

                    orderLinkId = None
                    order_status = None

                if by_psn_qty and sell_psn_qty:
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
                            set_trading_stop(bot, position_idx, takeProfit=str(count_dict['stop_price']), stopLoss=str(order_stop_loss))
                time.sleep(bot.time_sleep)
                continue

            else:
                # if order_side == 'Buy':
                #     order_stop_loss = mark_price - 2 * Decimal(bot.symbol.tickSize)
                # else:
                #     order_stop_loss = mark_price + 2 * Decimal(bot.symbol.tickSize)
                if order_side == 'Buy':
                    order_stop_loss = round(mark_price - (mark_price * leverage_trend), price_scale)
                else:
                    order_stop_loss = round(mark_price + (mark_price * leverage_trend), price_scale)

                order = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    side=order_side,
                    orderType="Limit",
                    qty=get_quantity_from_price(Decimal(str(bot.qty)), mark_price, bot.symbol.minOrderQty,
                                                bot.isLeverage),
                    price=mark_price,
                    takeProfit=str(count_dict['stop_price']),
                    stopLoss=str(order_stop_loss),
                )

                orderLinkId = order.orderLinkId

                # Инвертируем индекс позиции в зависимости от направления выставления плюсового ордера
                position_idx = 2 if order_side == 'Buy' else 1
                # Выставляем stopLoss для минусовой позиции
                set_trading_stop(bot, position_idx, stopLoss=str(count_dict['stop_price']))

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
