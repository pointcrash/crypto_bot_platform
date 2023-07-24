from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from api_v5 import get_order_status, get_query_account_coins_balance
from bots.bot_logic import logging
from bots.models import Bot, Process
from bots.terminate_bot_logic import terminate_process_by_pid, stop_bot_with_cancel_orders, \
    stop_bot_with_cancel_orders_and_drop_positions
from main.models import Account
from orders.models import Order


def views_bots_type_choice(request, mode):
    user = request.user
    category = 'linear' if mode == 'one-way' else 'inverse'

    if user.is_superuser:
        grid_bots = Bot.objects.filter(work_model='grid', category=category)
    else:
        grid_bots = Bot.objects.filter(owner=user, work_model='grid', category=category)

    if user.is_superuser:
        bb_bots = Bot.objects.filter(work_model='bb', category=category)
    else:
        bb_bots = Bot.objects.filter(owner=user, work_model='bb', category=category)

    if mode == 'hedge':
        title = 'Hedge Mode'
        return render(request, 'hedge/type_choice.html',
                      {'title': title, 'mode': mode, 'bb_bots': bb_bots, 'grid_bots': grid_bots, })
    elif mode == 'one-way':
        title = 'One-Way Mode'
        return render(request, 'one_way/type_choice.html',
                      {'title': title, 'mode': mode, 'bb_bots': bb_bots, 'grid_bots': grid_bots, })
    else:
        return redirect('/')


@login_required
def terminate_bot(request, bot_id, event_number):
    bot = Bot.objects.get(pk=bot_id)
    process = Process.objects.get(bot=bot)
    pid = process.pid

    if event_number == 1:
        logging(bot, terminate_process_by_pid(pid))

    elif event_number == 2:
        stop_bot_with_cancel_orders(bot)

    elif event_number == 3:
        stop_bot_with_cancel_orders_and_drop_positions(bot)

    process.pid = None
    process.save()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def delete_bot(request, bot_id, event_number):
    bot = Bot.objects.get(pk=bot_id)
    if event_number == 1:
        terminate_process_by_pid(bot.process_id)

    elif event_number == 2:
        stop_bot_with_cancel_orders(bot)

    elif event_number == 3:
        stop_bot_with_cancel_orders_and_drop_positions(bot)
    bot.delete()
    return redirect('single_bot_list')


def view_order_status(request, bot_id, order_id):
    bot = Bot.objects.get(pk=bot_id)
    order = Order.objects.get(pk=order_id)
    status = get_order_status(bot.account, bot.category, bot.symbol, order.orderLinkId)


def get_balance_views(request, acc_id):
    acc = Account.objects.get(pk=acc_id)
    balance = get_query_account_coins_balance(acc)
    return render(request, 'balance.html', {'balance': balance})


