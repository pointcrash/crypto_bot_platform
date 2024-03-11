import threading
from datetime import datetime

from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from api.api_v5_bybit import get_open_orders
from bots.bb_set_takes import set_takes
from bots.bot_logic import clear_data_bot, func_get_symbol_list
from bots.forms import BotForm, Set0PsnForm, OppositePositionForm
from bots.hedge.logic.ts_bb.entry import entry_ts_bb_bot
from bots.hedge.logic.work import set_takes_for_hedge_grid_bot
from bots.models import Bot, Set0Psn, OppositePosition

from bots.terminate_bot_logic import check_thread_alive, stop_bot_with_cancel_orders
from single_bot.logic.global_variables import lock, global_list_threads


@login_required
def single_bb_bot_create(request):
    title = 'Create BB Bot'

    if request.method == 'POST':
        bot_form = BotForm(request=request, data=request.POST)
        set0psn_form = Set0PsnForm(data=request.POST)
        opposite_psn_form = OppositePositionForm(data=request.POST)

        if bot_form.is_valid() and set0psn_form.is_valid() and opposite_psn_form.is_valid():
            bot = bot_form.save(commit=False)
            bot.work_model = 'bb'
            bot.owner = request.user
            bot.category = 'linear'
            bot.save()

            set0psn = set0psn_form.save(commit=False)
            set0psn.bot = bot
            set0psn.save()

            opposite_psn = opposite_psn_form.save(commit=False)
            opposite_psn.bot = bot
            opposite_psn.save()

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
        opposite_psn_form = OppositePositionForm()

    return render(request, 'one_way/create_bot.html', {
        'form': bot_form,
        'set0psn_form': set0psn_form,
        'opposite_psn_form': opposite_psn_form,
        'title': title,
    })


@login_required
def single_bb_bot_detail(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    set0psn = Set0Psn.objects.filter(bot=bot).first()
    opposite_psn = OppositePosition.objects.filter(bot=bot).first()
    symbol_list = func_get_symbol_list(bot)
    symbol_list = symbol_list[0] if float(symbol_list[0]['size']) > 0 else symbol_list[1]
    if request.method == 'POST':
        bot_form = BotForm(request.POST, request=request, instance=bot)
        if set0psn:
            set0psn_form = Set0PsnForm(data=request.POST, instance=set0psn)
        else:
            set0psn_form = Set0PsnForm(data=request.POST)
        if opposite_psn:
            opposite_psn_form = OppositePositionForm(data=request.POST, instance=opposite_psn)
        else:
            opposite_psn_form = OppositePositionForm(data=request.POST)

        if bot_form.is_valid() and set0psn_form.is_valid() and opposite_psn_form.is_valid():

            bot = bot_form.save(commit=False)
            clear_data_bot(bot)

            set0psn_form.save(commit=False)
            set0psn.bot = bot
            set0psn.save()

            opposite_psn = opposite_psn_form.save(commit=False)
            opposite_psn.bot = bot
            opposite_psn.save()

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
        if opposite_psn:
            opposite_psn_form = OppositePositionForm(instance=opposite_psn)
        else:
            opposite_psn_form = OppositePositionForm()

    order_list_status, order_list = get_open_orders(bot)
    for order in order_list:
        time = int(order['updatedTime'])
        dt_object = datetime.fromtimestamp(time / 1000.0)
        formatted_date = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        order['updatedTime'] = formatted_date

    return render(request, 'one_way/bb/bot_detail.html', {
                                                                        'form': bot_form,
                                                                        'set0psn_form': set0psn_form,
                                                                        'opposite_psn_form': opposite_psn_form,
                                                                        'bot': bot,
                                                                        'symbol_list': symbol_list,
                                                                        'order_list': order_list,
                                                                    })
