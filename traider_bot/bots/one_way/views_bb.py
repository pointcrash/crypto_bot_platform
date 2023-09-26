import threading
from datetime import datetime

from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from api_v5 import get_open_orders
from bots.bb_set_takes import set_takes
from bots.bot_logic import clear_data_bot, func_get_symbol_list
from bots.forms import BotForm, Set0PsnForm
from bots.hedge.logic.ts_bb.entry import entry_ts_bb_bot
from bots.hedge.logic.work import set_takes_for_hedge_grid_bot
from bots.models import Bot, Set0Psn

from bots.terminate_bot_logic import check_thread_alive, stop_bot_with_cancel_orders
from single_bot.logic.global_variables import lock, global_list_threads


@login_required
def single_bb_bot_create(request):
    title = 'Create BB Bot'

    if request.method == 'POST':
        bot_form = BotForm(request=request, data=request.POST)
        set0psn_form = Set0PsnForm(data=request.POST)

        if bot_form.is_valid() and set0psn_form.is_valid():
            bot = bot_form.save(commit=False)
            bot.work_model = 'bb'
            bot.owner = request.user
            bot.category = 'linear'
            bot.save()

            set0psn = set0psn_form.save(commit=False)
            set0psn.bot = bot
            set0psn.save()

            connections.close_all()

            if bot.side == 'TS':
                bot_thread = threading.Thread(target=entry_ts_bb_bot, args=(bot,))
            else:
                bot_thread = threading.Thread(target=set_takes, args=(bot,))
            bot_thread.start()

            lock.acquire()
            global_list_threads[bot.pk] = bot_thread
            if lock.locked():
                lock.release()

            return redirect('single_bot_list')
    else:
        bot_form = BotForm(request=request)
        set0psn_form = Set0PsnForm()

    return render(request, 'one_way/create_bot.html', {'form': bot_form, 'set0psn_form': set0psn_form, 'title': title, })


@login_required
def single_bb_bot_detail(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    set0psn = Set0Psn.objects.filter(bot=bot).first()
    symbol_list = func_get_symbol_list(bot)
    symbol_list = symbol_list[0] if float(symbol_list[0]['size']) > 0 else symbol_list[1]
    if request.method == 'POST':
        bot_form = BotForm(request.POST, request=request, instance=bot)
        if set0psn:
            set0psn_form = Set0PsnForm(data=request.POST, instance=set0psn)
        else:
            set0psn_form = Set0PsnForm(data=request.POST)

        if bot_form.is_valid() and set0psn_form.is_valid():

            bot = bot_form.save(commit=False)
            clear_data_bot(bot)
            set0psn_form.save()

            if check_thread_alive(bot.pk):
                stop_bot_with_cancel_orders(bot)

            if bot.side == 'TS':
                bot_thread = threading.Thread(target=entry_ts_bb_bot, args=(bot,))
            else:
                bot_thread = threading.Thread(target=set_takes, args=(bot,))

            bot_thread.start()
            bot.is_active = True
            bot.save()

            lock.acquire()
            global_list_threads[bot.pk] = bot_thread
            if lock.locked():
                lock.release()

            return redirect('single_bot_list')
    else:
        bot_form = BotForm(request=request, instance=bot)
        if set0psn:
            set0psn_form = Set0PsnForm(instance=set0psn)
        else:
            set0psn_form = Set0PsnForm()

    order_list = get_open_orders(bot)
    for order in order_list:
        time = int(order['updatedTime'])
        dt_object = datetime.fromtimestamp(time / 1000.0)
        formatted_date = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        order['updatedTime'] = formatted_date

    return render(request, 'one_way/bb/bot_detail.html',
                  {'form': bot_form, 'set0psn_form': set0psn_form, 'bot': bot, 'symbol_list': symbol_list, 'order_list': order_list, })
