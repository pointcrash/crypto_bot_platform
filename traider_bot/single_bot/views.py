import threading
from datetime import datetime

from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from api_v5 import get_open_orders
from bots.SimpleHedge.logic.main_logic import simple_hedge_bot_main_logic
from bots.bb_set_takes import set_takes
from bots.hedge.logic.work import set_takes_for_hedge_grid_bot
from bots.terminate_bot_logic import stop_bot_with_cancel_orders, check_thread_alive
from bots.bot_logic import get_update_symbols, clear_data_bot, func_get_symbol_list
from bots.forms import GridBotForm, Set0PsnForm
from bots.models import Bot, IsTSStart, Set0Psn, SimpleHedge
from main.forms import AccountSelectForm

from single_bot.logic.global_variables import lock, global_list_bot_id, global_list_threads
from single_bot.logic.work import bot_work_logic, append_thread_or_check_duplicate


@login_required
def single_bot_list(request):
    user = request.user

    if user.is_superuser:
        bots = Bot.objects.all().order_by('pk')
        all_bots_pks = Bot.objects.values_list('pk', flat=True).order_by('pk')
    else:
        bots = Bot.objects.filter(owner=user).order_by('pk')
        all_bots_pks = Bot.objects.filter(owner=user).values_list('pk', flat=True).order_by('pk')

    if request.method == 'POST':
        account_select_form = AccountSelectForm(request.POST, user=request.user)
        if account_select_form.is_valid():
            selected_account = account_select_form.cleaned_data['account']
            if selected_account:
                bots = bots.filter(account=selected_account)
                all_bots_pks = bots.values_list('pk', flat=True).order_by('pk')
    else:
        account_select_form = AccountSelectForm(user=request.user)

    is_alive_list = []

    lock.acquire()
    try:
        for bot_id in all_bots_pks:
            if bot_id in global_list_bot_id:
                is_alive_list.append(True)
            else:
                is_alive_list.append(False)
    finally:
        lock.release()
    bots = zip(bots, is_alive_list)

    return render(request, 'bot_list.html', {'bots': bots, 'account_select_form': account_select_form, })


@login_required
def single_bot_create(request):
    title = 'Create Bot'

    if request.method == 'POST':
        bot_form = GridBotForm(request=request, data=request.POST)
        set0psn_form = Set0PsnForm(data=request.POST)

        if bot_form.is_valid() and set0psn_form.is_valid():
            bot = bot_form.save(commit=False)
            bot.work_model = 'grid'
            bot.owner = request.user
            bot.category = 'linear'
            bot.save()

            set0psn = set0psn_form.save(commit=False)
            set0psn.bot = bot
            set0psn.save()

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
        bot_form = GridBotForm(request=request)
        set0psn_form = Set0PsnForm()

    return render(request, 'create_bot.html', {'form': bot_form, 'title': title, 'set0psn_form': set0psn_form, })


@login_required
def single_bot_detail(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    set0psn = Set0Psn.objects.filter(bot=bot).first()
    symbol_list = func_get_symbol_list(bot)
    symbol_list = symbol_list[0] if float(symbol_list[0]['size']) > 0 else symbol_list[1]
    symbol_list['avgPrice'] = round(float(symbol_list['avgPrice']), 2)
    symbol_list['unrealisedPnl'] = round(float(symbol_list['unrealisedPnl']), 2)
    symbol_list['positionBalance'] = round(float(symbol_list['positionBalance']), 2)
    if request.method == 'POST':
        bot_form = GridBotForm(request.POST, request=request, instance=bot)
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
        bot_form = GridBotForm(request=request, instance=bot)
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
        print(order)

    return render(request, 'bot_detail.html',
                  {'form': bot_form, 'set0psn_form': set0psn_form, 'bot': bot, 'symbol_list': symbol_list, 'order_list': order_list})


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

    elif bot.work_model == 'SmpHg':
        simple_hedge = SimpleHedge.objects.filter(bot=bot).first()
        bot_thread = threading.Thread(target=simple_hedge_bot_main_logic, args=(bot, simple_hedge))
        append_thread_or_check_duplicate(bot.pk)

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
