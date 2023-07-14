import multiprocessing

from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from api_v5 import get_order_status, get_balance, get_query_account_coins_balance
from bots.terminate_bot_logic import terminate_process_by_pid, get_status_process, stop_bot_with_cancel_orders, \
    stop_bot_with_cancel_orders_and_drop_positions
from main.models import Account
from orders.models import Order
from .bot_logic import create_bb_and_avg_obj, logging
from .bb_set_takes import set_takes
from .forms import BotForm
from .models import Bot, Process
from django.contrib import messages


@login_required
def bb_create_bot(request):
    title = 'Bollinger Bands Bot'
    if request.method == 'POST':
        form = BotForm(user=request.user, data=request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            bot.work_model = 'bb'
            bot.owner = request.user
            bot.save()
            bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot)
            connections.close_all()
            logging(bot, 'started work in')

            bot_process = multiprocessing.Process(target=set_takes, args=(bot, bb_obj, bb_avg_obj))
            bot_process.start()
            bot.process_id = str(bot_process.pid)
            bot.save()

            return redirect('bb_bots_list')
    else:
        form = BotForm(user=request.user)

    return render(request, 'create_bot.html', {'form': form, 'title': title})


@login_required
def bb_bots_list(request):
    user = request.user
    if user.is_superuser:
        bots = Bot.objects.filter(work_model='bb')
    else:
        bots = Bot.objects.filter(owner=user, work_model='bb')
    is_alive_list = []
    for bot in bots:
        if bot.process_id is not None:
            is_alive_list.append(get_status_process(bot.process_id))
        else:
            is_alive_list.append(None)

    bots = zip(bots, is_alive_list)
    return render(request, 'bb_bots_list.html', {'bots': bots})


@login_required
def bb_bot_detail(request, bot_id):
    message = []
    error_message = messages.get_messages(request)
    if error_message:
        message.append(error_message)
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        form = BotForm(request.POST, instance=bot)  # Передаем экземпляр модели в форму
        if form.is_valid():
            bot = form.save()
            if get_status_process(bot.process_id):
                terminate_process_by_pid(bot.process_id)
            bot_process = multiprocessing.Process(target=set_takes, args=(bot,))
            bot_process.start()
            bot.process_id = str(bot_process.pid)
            bot.save()
            return redirect('bb_bots_list')
    else:
        form = BotForm(user=request.user, instance=bot)  # Передаем экземпляр модели в форму

    return render(request, 'bot_detail.html', {'form': form, 'bot': bot, 'message': message})


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
    return redirect('bb_bots_list')


@login_required
def delete_bot(request, bot_id, event_number, redirect_to):
    bot = Bot.objects.get(pk=bot_id)
    if event_number == 1:
        terminate_process_by_pid(bot.process_id)

    elif event_number == 2:
        stop_bot_with_cancel_orders(bot)

    elif event_number == 3:
        stop_bot_with_cancel_orders_and_drop_positions(bot)
    bot.delete()
    if redirect_to == 'grid':
        return redirect('grid_bots_list')
    else:
        return redirect('bb_bots_list')


def view_order_status(request, bot_id, order_id):
    bot = Bot.objects.get(pk=bot_id)
    order = Order.objects.get(pk=order_id)
    status = get_order_status(bot.account, bot.category, bot.symbol, order.orderLinkId)


def get_balance_views(request, acc_id):
    acc = Account.objects.get(pk=acc_id)
    balance = get_query_account_coins_balance(acc)
    return render(request, 'balance.html', {'balance': balance})
