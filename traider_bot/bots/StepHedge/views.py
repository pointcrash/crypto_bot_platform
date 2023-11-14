import threading
from datetime import datetime

from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from api_v5 import get_open_orders
from bots.StepHedge.forms import BotForm, StepHedgeForm
from bots.StepHedge.logic.main_logic import step_hedge_bot_main_logic
from bots.StepHedge.ws_logic.main_logic import ws_step_hedge_bot_main_logic
from bots.bot_logic import clear_data_bot, func_get_symbol_list
from bots.models import Bot, StepHedge
from bots.terminate_bot_logic import check_thread_alive, stop_bot_with_cancel_orders, terminate_thread
from main.models import ActiveBot
from single_bot.logic.global_variables import lock, global_list_threads
from single_bot.logic.work import append_thread_or_check_duplicate


@login_required
def step_hedge_bot_create(request):
    title = 'Create Step Hedge Bot'

    if request.method == 'POST':
        bot_form = BotForm(request=request, data=request.POST)
        step_hedge_form = StepHedgeForm(data=request.POST)

        if bot_form.is_valid() and step_hedge_form.is_valid():
            bot = bot_form.save(commit=False)
            bot.work_model = 'Step Hedge'
            bot.owner = request.user
            bot.category = 'linear'
            bot.qty = 1
            bot.save()

            step_hedge = step_hedge_form.save(commit=False)
            step_hedge.bot = bot
            # step_hedge.tppp = step_hedge.tppp.replace(',', '.') if ',' in step_hedge.tppp else step_hedge.tppp
            # step_hedge.tpap = step_hedge.tpap.replace(',', '.') if ',' in step_hedge.tpap else step_hedge.tpap
            step_hedge.save()

            connections.close_all()

            bot_thread = threading.Thread(target=ws_step_hedge_bot_main_logic, args=(bot, step_hedge))
            bot_thread.start()

            append_thread_or_check_duplicate(bot.pk)
            # if not ActiveBot.objects.filter(bot_id=bot.pk).first():
            #     ActiveBot.objects.create(bot_id=bot.pk)
            lock.acquire()
            global_list_threads[bot.pk] = bot_thread
            if lock.locked():
                lock.release()

            return redirect('single_bot_list')
    else:
        bot_form = BotForm(request=request)
        step_hedge_form = StepHedgeForm()

    return render(request, 'step_hedge/create.html',
                  {'form': bot_form, 'step_hedge_form': step_hedge_form, 'title': title, })


@login_required
def step_hedge_bot_detail(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    step_hedge = StepHedge.objects.filter(bot=bot).first()
    symbol_list = func_get_symbol_list(bot)
    try:
        have_open_psn = True if float(symbol_list[0]['size']) or float(symbol_list[1]['size']) else False
    except:
        have_open_psn = False

    if request.method == 'POST':
        bot_form = BotForm(request.POST, request=request, instance=bot)
        step_hedge_form = StepHedgeForm(data=request.POST, instance=step_hedge)

        if bot_form.is_valid() and step_hedge_form.is_valid():

            bot = bot_form.save(commit=False)
            clear_data_bot(bot)
            step_hedge = step_hedge_form.save(commit=False)
            # step_hedge.tppp = step_hedge.tppp.replace(',', '.') if ',' in step_hedge.tppp else step_hedge.tppp
            # step_hedge.tpap = step_hedge.tpap.replace(',', '.') if ',' in step_hedge.tpap else step_hedge.tpap
            step_hedge.save()

            if check_thread_alive(bot.pk):
                terminate_thread(bot.pk)

            bot_thread = threading.Thread(target=ws_step_hedge_bot_main_logic, args=(bot, step_hedge))

            bot_thread.start()
            # bot.is_active = True
            bot.save()

            if not ActiveBot.objects.filter(bot_id=bot.pk):
                ActiveBot.objects.create(bot_id=bot.pk)
            # append_thread_or_check_duplicate(bot.pk)
            lock.acquire()
            global_list_threads[bot.pk] = bot_thread
            if lock.locked():
                lock.release()

            return redirect('single_bot_list')
    else:
        bot_form = BotForm(request=request, instance=bot)
        step_hedge_form = StepHedgeForm(instance=step_hedge)

    status, order_list = get_open_orders(bot)
    for order in order_list:
        time = int(order['updatedTime'])
        dt_object = datetime.fromtimestamp(time / 1000.0)
        formatted_date = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        order['updatedTime'] = formatted_date
        order['price'] = float(order['price']) if order['price'] else order['price']
        order['triggerPrice'] = float(order['triggerPrice']) if order['triggerPrice'] else order['triggerPrice']
        order['takeProfit'] = float(order['takeProfit']) if order['takeProfit'] else order['takeProfit']
        order['stopLoss'] = float(order['stopLoss']) if order['stopLoss'] else order['stopLoss']

    return render(request, 'step_hedge/detail.html',
                  {
                      'form': bot_form,
                      'step_hedge_form': step_hedge_form,
                      'bot': bot,
                      'order_list': order_list,
                      'symbol_list': symbol_list,
                      'have_open_psn': have_open_psn,
                  })
