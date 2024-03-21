import threading
from datetime import datetime

from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from api.api_v5_bybit import get_open_orders
from bots.SimpleHedge.logic.main_logic import simple_hedge_bot_main_logic
from bots.SimpleHedge.logic.manual_average import manual_average_for_simple_hedge
from bots.bot_logic import clear_data_bot, custom_logging, func_get_symbol_list
from bots.forms import BotForm, SimpleHedgeForm
from bots.models import Bot, SimpleHedge
from bots.terminate_bot_logic import check_thread_alive, stop_bot_with_cancel_orders
from single_bot.logic.global_variables import lock, global_list_threads
from single_bot.logic.work import append_thread_or_check_duplicate


@login_required
def simple_hedge_bot_create(request):
    title = 'Create Simple Hedge Bot'

    if request.method == 'POST':
        bot_form = BotForm(request=request, data=request.POST)
        simple_hedge_form = SimpleHedgeForm(data=request.POST)

        if bot_form.is_valid() and simple_hedge_form.is_valid():
            bot = bot_form.save(commit=False)
            bot.work_model = 'SmpHg'
            bot.owner = request.user
            bot.category = 'linear'
            bot.save()

            simple_hedge = simple_hedge_form.save(commit=False)
            simple_hedge.bot = bot
            simple_hedge.tppp = simple_hedge.tppp.replace(',', '.') if ',' in simple_hedge.tppp else simple_hedge.tppp
            simple_hedge.tpap = simple_hedge.tpap.replace(',', '.') if ',' in simple_hedge.tpap else simple_hedge.tpap
            simple_hedge.save()

            connections.close_all()

            bot_thread = threading.Thread(target=simple_hedge_bot_main_logic, args=(bot, simple_hedge))
            bot_thread.start()

            append_thread_or_check_duplicate(bot.pk)
            lock.acquire()
            global_list_threads[bot.pk] = bot_thread
            if lock.locked():
                lock.release()

            return redirect('single_bot_list')
    else:
        bot_form = BotForm(request=request)
        simple_hedge_form = SimpleHedgeForm()

    return render(request, 'simple_hedge/create.html',
                  {'form': bot_form, 'simple_hedge_form': simple_hedge_form, 'title': title, })


@login_required
def simple_hedge_bot_detail(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    simple_hedge = SimpleHedge.objects.filter(bot=bot).first()
    symbol_list = func_get_symbol_list(bot)
    try:
        have_open_psn = True if float(symbol_list[0]['size']) or float(symbol_list[1]['size']) else False
    except:
        have_open_psn = False

    if request.method == 'POST':
        bot_form = BotForm(request.POST, request=request, instance=bot)
        simple_hedge_form = SimpleHedgeForm(data=request.POST, instance=simple_hedge)

        if bot_form.is_valid() and simple_hedge_form.is_valid():

            bot = bot_form.save(commit=False)
            clear_data_bot(bot)
            simple_hedge = simple_hedge_form.save(commit=False)
            simple_hedge.tppp = simple_hedge.tppp.replace(',', '.') if ',' in simple_hedge.tppp else simple_hedge.tppp
            simple_hedge.tpap = simple_hedge.tpap.replace(',', '.') if ',' in simple_hedge.tpap else simple_hedge.tpap
            simple_hedge.save()

            if check_thread_alive(bot.pk):
                stop_bot_with_cancel_orders(bot)

            bot_thread = threading.Thread(target=simple_hedge_bot_main_logic, args=(bot, simple_hedge))

            bot_thread.start()
            bot.is_active = True
            bot.save()

            append_thread_or_check_duplicate(bot.pk)
            lock.acquire()
            global_list_threads[bot.pk] = bot_thread
            if lock.locked():
                lock.release()

            return redirect('single_bot_list')
    else:
        bot_form = BotForm(request=request, instance=bot)
        simple_hedge_form = SimpleHedgeForm(instance=simple_hedge)

    status, order_list = get_open_orders(bot)
    for order in order_list:
        time = int(order['updatedTime'])
        dt_object = datetime.fromtimestamp(time / 1000.0)
        formatted_date = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        order['updatedTime'] = formatted_date

    return render(request, 'simple_hedge/detail.html',
                  {
                      'form': bot_form,
                      'simple_hedge_form': simple_hedge_form,
                      'bot': bot,
                      'order_list': order_list,
                      'symbol_list': symbol_list,
                      'have_open_psn': have_open_psn,
                  })


def averaging_simple_hedge_view(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        is_percent = request.POST.get('is_percent')
        is_percent = True if is_percent else False
        amount = request.POST.get('amount')
        price = request.POST.get('price')
        if not amount.isdigit():
            custom_logging(bot, f'Введено неверное значение AMOUNT ({amount}) для усреднения')
            return redirect(request.META.get('HTTP_REFERER'))

        manual_average_for_simple_hedge(bot, amount, is_percent, price)

        return redirect(request.META.get('HTTP_REFERER'))

    else:
        pass
