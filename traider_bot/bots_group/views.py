import threading
from copy import copy
from datetime import datetime
import time

from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from api_test.api_v5_bybit import get_open_orders
from bots.StepHedge.logic.main_logic import step_hedge_bot_main_logic
from bots.StepHedge.ws_logic.main_logic import ws_step_hedge_bot_main_logic
from bots.general_functions import clear_data_bot, func_get_symbol_list, is_bot_active, custom_logging
from bots.models import Bot, StepHedge
from bots.terminate_bot_logic import check_thread_alive, stop_bot_with_cancel_orders, terminate_thread
from bots_group.forms import BotForm, StepHedgeForm
from bots_group.models import BotsGroup
from main.forms import AccountSelectForm
from main.logic import calculate_pnl
from main.models import ActiveBot
from single_bot.logic.global_variables import lock, global_list_threads
from single_bot.logic.work import append_thread_or_check_duplicate
from concurrent.futures import ThreadPoolExecutor


@login_required
def bots_groups_list(request):
    user = request.user
    bots_groups = dict()

    if user.is_superuser:
        for group in BotsGroup.objects.all():
            group_elem = []
            for bot in group.bot_set.all():
                group_elem.append((bot, True if ActiveBot.objects.filter(bot_id=bot.pk).first() else False))
            bots_groups[group] = group_elem
    else:
        for group in BotsGroup.objects.filter(owner=user).order_by('pk'):
            group_elem = []
            for bot in group.bot_set.all():
                group_elem.append((bot, True if ActiveBot.objects.filter(bot_id=bot.pk).first() else False))
            bots_groups[group] = group_elem

    # for bot in bots:
    #     pnl = calculate_pnl(bot=bot, start_date=bot.time_create, end_date=datetime.now())
    #     pnl_list.append(pnl)

    print(bots_groups)
    if request.method == 'POST':
        pass
    else:
        account_select_form = AccountSelectForm(user=request.user)

    return render(request, 'bots_group_list.html', {
        'bots_groups': bots_groups,
    })


@login_required
def group_step_hedge_bot_create(request):
    title = 'Create Step Hedge Bot'

    if request.method == 'POST':
        bot_form = BotForm(request=request, data=request.POST)
        step_hedge_form = StepHedgeForm(data=request.POST)

        if bot_form.is_valid() and step_hedge_form.is_valid():
            selected_accounts = bot_form.cleaned_data['accounts_list']

            for index, account in enumerate(selected_accounts):
                if index == 0:
                    bot = bot_form.save(commit=False)

                    group = BotsGroup.objects.create(name=bot.symbol, owner=request.user)

                    bot.group = group
                    bot.work_model = 'Step Hedge'
                    bot.owner = request.user
                    bot.account = account
                    bot.category = 'linear'
                    bot.qty = 1
                    bot.save()

                    step_hedge = step_hedge_form.save(commit=False)
                    step_hedge.bot = bot
                    step_hedge.save()
                else:
                    bot = copy(bot)
                    bot.pk = None
                    bot.account = account
                    bot.group = group
                    bot.save()

                    step_hedge = copy(step_hedge)
                    step_hedge.pk = None
                    step_hedge.bot = bot
                    step_hedge.save()

                if not ActiveBot.objects.filter(bot_id=bot.pk):
                    ActiveBot.objects.create(bot_id=bot.pk)

                connections.close_all()

                bot_thread = threading.Thread(target=ws_step_hedge_bot_main_logic, args=(bot, step_hedge))
                bot_thread.start()

                lock.acquire()
                global_list_threads[bot.pk] = bot_thread
                if lock.locked():
                    lock.release()

            return redirect('bots_groups_list')
    else:
        bot_form = BotForm(request=request)
        step_hedge_form = StepHedgeForm()

    return render(request, 'step_hedge/create_group.html',
                  {'form': bot_form, 'step_hedge_form': step_hedge_form, 'title': title, })


# @login_required
# def step_hedge_bot_detail(request, bot_id):
#     bot = Bot.objects.get(pk=bot_id)
#     step_hedge = StepHedge.objects.filter(bot=bot).first()
#     symbol_list = func_get_symbol_list(bot)
#     try:
#         have_open_psn = True if float(symbol_list[0]['size']) or float(symbol_list[1]['size']) else False
#     except:
#         have_open_psn = False
#
#     if request.method == 'POST':
#         bot_form = BotForm(request.POST, request=request, instance=bot)
#         step_hedge_form = StepHedgeForm(data=request.POST, instance=step_hedge)
#
#         if bot_form.is_valid() and step_hedge_form.is_valid():
#
#             bot = bot_form.save(commit=False)
#             step_hedge = step_hedge_form.save(commit=False)
#             step_hedge.save()
#             bot.is_active = True
#             bot.save()
#
#             terminate_thread(bot_id)
#             bot_thread = threading.Thread(target=ws_step_hedge_bot_main_logic, args=(bot, step_hedge))
#             if not is_bot_active(bot.pk):
#                 ActiveBot.objects.create(bot_id=bot.pk)
#                 bot_thread.start()
#
#             return redirect('single_bot_list')
#     else:
#         bot_form = BotForm(request=request, instance=bot)
#         step_hedge_form = StepHedgeForm(instance=step_hedge)
#
#     status, order_list = get_open_orders(bot)
#     for order in order_list:
#         time = int(order['updatedTime'])
#         dt_object = datetime.fromtimestamp(time / 1000.0)
#         formatted_date = dt_object.strftime("%Y-%m-%d %H:%M:%S")
#         order['updatedTime'] = formatted_date
#         order['price'] = float(order['price']) if order['price'] else order['price']
#         order['triggerPrice'] = float(order['triggerPrice']) if order['triggerPrice'] else order['triggerPrice']
#         order['takeProfit'] = float(order['takeProfit']) if order['takeProfit'] else order['takeProfit']
#         order['stopLoss'] = float(order['stopLoss']) if order['stopLoss'] else order['stopLoss']
#
#     if bot.time_update:
#         pnl_list = calculate_pnl(bot=bot, start_date=bot.time_create, end_date=datetime.now())
#
#     return render(request, 'step_hedge/detail.html',
#                   {
#                       'form': bot_form,
#                       'step_hedge_form': step_hedge_form,
#                       'bot': bot,
#                       'order_list': order_list,
#                       'symbol_list': symbol_list,
#                       'have_open_psn': have_open_psn,
#                       'move_nipple': step_hedge.move_nipple,
#                       'pnl_list': pnl_list,
#                   })

# def stop_group(request, group_id):
#     group = BotsGroup.objects.get(pk=group_id)
#     bots = group.bot_set.all()
#
#     with ThreadPoolExecutor() as executor:
#         executor.map(some_averaging_function, bots)
#     return redirect(request.META.get('HTTP_REFERER'))


def stop_group(request, group_id):
    group = BotsGroup.objects.get(pk=group_id)
    bots = group.bot_set.all()

    def stop_bot(bot):
        custom_logging(bot, terminate_thread(bot.pk))

    with ThreadPoolExecutor() as executor:
        executor.map(stop_bot, bots)
    return redirect(request.META.get('HTTP_REFERER'))


def delete_group(request, group_id):
    group = BotsGroup.objects.get(pk=group_id)
    group.delete()
    return redirect(request.META.get('HTTP_REFERER'))
