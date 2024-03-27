import threading

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.bb_set_takes import set_takes
from bots.bot_logic import clear_data_bot
from bots.hedge.logic.work import set_takes_for_hedge_grid_bot
from bots.models import IsTSStart, BotModel
from bots.terminate_bot_logic import terminate_bot, terminate_bot_with_cancel_orders, \
    terminate_bot_with_cancel_orders_and_drop_positions
from main.forms import AccountSelectForm
from main.models import ActiveBot
from single_bot.logic.global_variables import global_list_threads, lock
from single_bot.logic.work import bot_work_logic


@login_required
def bot_list(request):
    user = request.user

    if user.is_superuser:
        bots = BotModel.objects.all().order_by('pk')
    else:
        bots = BotModel.objects.filter(owner=user).order_by('pk')

    if request.method == 'POST':
        account_select_form = AccountSelectForm(request.POST, user=request.user)
        if account_select_form.is_valid():
            selected_account = account_select_form.cleaned_data['account']
            if selected_account:
                bots = bots.filter(account=selected_account)
    else:
        account_select_form = AccountSelectForm(user=request.user)

    return render(request, 'bot_list.html', {
        'bots': bots,
        'account_select_form': account_select_form,
    })


def views_bots_type_choice(request, mode):
    user = request.user
    category = 'linear' if mode == 'one-way' else 'inverse'

    if user.is_superuser:
        grid_bots = BotModel.objects.filter(work_model='grid', category=category)
    else:
        grid_bots = BotModel.objects.filter(owner=user, work_model='grid', category=category)

    if user.is_superuser:
        bb_bots = BotModel.objects.filter(work_model='bb', category=category)
    else:
        bb_bots = BotModel.objects.filter(owner=user, work_model='bb', category=category)

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
def stop_bot(request, bot_id, event_number):
    bot = BotModel.objects.get(pk=bot_id)

    if event_number == 1:
        terminate_bot(bot)
    elif event_number == 2:
        terminate_bot_with_cancel_orders(bot)
    elif event_number == 3:
        terminate_bot_with_cancel_orders_and_drop_positions(bot)

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def delete_bot(request, bot_id, event_number):
    bot = BotModel.objects.get(pk=bot_id)

    if event_number == 1:
        terminate_bot(bot)
    elif event_number == 2:
        terminate_bot_with_cancel_orders(bot)
    elif event_number == 3:
        terminate_bot_with_cancel_orders_and_drop_positions(bot)

    bot.delete()

    return redirect(request.META.get('HTTP_REFERER'))


def reboot_bots(request):
    bots = BotModel.objects.all()
    for bot in bots:
        print(bot.is_active)
        if bot.is_active:
            bot_thread = None
            is_ts_start = IsTSStart.objects.filter(bot=bot)

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
    return redirect('bot_list')
