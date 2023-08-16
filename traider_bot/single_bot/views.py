import threading

from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.bb_set_takes import set_takes
from bots.hedge.logic.work import set_takes_for_hedge_grid_bot
from bots.terminate_bot_logic import terminate_thread, stop_bot_with_cancel_orders, check_thread_alive
from bots.bot_logic import get_update_symbols, create_bb_and_avg_obj, clean_and_return_bot_object, clear_data_bot
from bots.forms import GridBotForm
from bots.bot_logic_grid import set_takes_for_grid_bot
from bots.models import Bot, Process, AvgOrder, Take, SingleBot, IsTSStart
from django.contrib import messages

from single_bot.logic.global_variables import lock, global_list_bot_id, global_list_threads
from single_bot.logic.work import bot_work_logic


@login_required
def single_bot_list(request):
    user = request.user
    if user.is_superuser:
        bots = Bot.objects.all().order_by('pk')
        all_bots_pks = Bot.objects.values_list('pk', flat=True).order_by('pk')
    else:
        bots = Bot.objects.filter(owner=user).order_by('pk')
        all_bots_pks = Bot.objects.filter(owner=user).values_list('pk', flat=True).order_by('pk')
    is_alive_list = []

    lock.acquire()
    try:
        # print(global_list_bot_id)
        # print(global_list_bot_id)
        # print(global_list_bot_id)
        # print(global_list_bot_id)
        for bot_id in all_bots_pks:
            if bot_id in global_list_bot_id:
                is_alive_list.append(True)
            else:
                is_alive_list.append(False)
    finally:
        lock.release()
    # print(is_alive_list)
    # print(is_alive_list)
    # print(is_alive_list)
    # print(is_alive_list)
    bots = zip(bots, is_alive_list)

    return render(request, 'bot_list.html', {'bots': bots, })


@login_required
def single_bot_create(request):
    title = 'Create Bot'

    if request.method == 'POST':
        form = GridBotForm(request=request, data=request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            bot.work_model = 'grid'
            bot.owner = request.user
            bot.category = 'inverse'
            bot.save()

            connections.close_all()

            if bot.side == 'TS':
                bot_thread = threading.Thread(target=set_takes_for_hedge_grid_bot, args=(bot,))
            else:
                bot_thread = threading.Thread(target=bot_work_logic, args=(bot,))
            bot_thread.start()
            lock.acquire()
            global_list_threads[bot.pk] = bot_thread
            lock.release()

            return redirect('single_bot_list')
    else:
        form = GridBotForm(request=request)

    return render(request, 'create_bot.html', {'form': form, 'title': title, })


@login_required
def single_bot_detail(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        form = GridBotForm(request.POST, request=request, instance=bot)
        if form.is_valid():
            bot = form.save(commit=False)
            clear_data_bot(bot)

            if check_thread_alive(bot.pk):
                stop_bot_with_cancel_orders(bot)

            if bot.side == 'TS':
                bot_thread = threading.Thread(target=set_takes_for_hedge_grid_bot, args=(bot,))
            else:
                bot_thread = threading.Thread(target=bot_work_logic, args=(bot,))

            bot_thread.start()
            bot.is_active = True
            bot.save()

            lock.acquire()
            global_list_threads[bot.pk] = bot_thread
            if lock.locked():
                lock.release()

            return redirect('single_bot_list')
    else:
        form = GridBotForm(request=request, instance=bot)

    return render(request, 'bot_detail.html', {'form': form, 'bot': bot, })


def bot_start(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    bot_thread = None
    is_ts_start = IsTSStart.objects.filter(bot=bot)

    if check_thread_alive(bot.pk):
        stop_bot_with_cancel_orders(bot)

    clear_data_bot(bot, clear_data=1)  # Очищаем данные ордеров и тейков которые использовал старый бот

    if bot.work_model == 'bb':
        if bot.side == 'TS':
            if is_ts_start:
                bot_thread = threading.Thread(target=set_takes, args=(bot,))
            else:
                bot_thread = threading.Thread(target=set_takes_for_hedge_grid_bot, args=(bot,))
        else:
            bot_thread = threading.Thread(target=set_takes, args=(bot,))
    elif bot.work_model == 'grid':
        if bot.side == 'TS':
            if is_ts_start:
                bot_thread = threading.Thread(target=bot_work_logic, args=(bot,))
            else:
                bot_thread = threading.Thread(target=set_takes_for_hedge_grid_bot, args=(bot,))
        else:
            bot_thread = threading.Thread(target=bot_work_logic, args=(bot,))

    if bot_thread is not None:
        bot_thread.start()
        bot.is_active = True
        bot.save()
        lock.acquire()
        global_list_threads[bot.pk] = bot_thread
        if lock.locked():
            lock.release()
    return redirect('single_bot_list')


def update_symbols_set(request):
    get_update_symbols()
    return redirect(request.META.get('HTTP_REFERER'))
