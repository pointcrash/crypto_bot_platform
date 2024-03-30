import threading

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.bb.logic.start_logic import bb_worker
from bots.models import BotModel
from bots.terminate_bot_logic import terminate_bot, terminate_bot_with_cancel_orders, \
    terminate_bot_with_cancel_orders_and_drop_positions
from main.forms import AccountSelectForm


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
    user = request.user

    if event_number == 1:
        terminate_bot(bot, user)
    elif event_number == 2:
        terminate_bot_with_cancel_orders(bot, user)
    elif event_number == 3:
        terminate_bot_with_cancel_orders_and_drop_positions(bot, user)

    bot.delete()

    return redirect(request.META.get('HTTP_REFERER'))


def bot_start(request, bot_id):
    bot = BotModel.objects.get(pk=bot_id)
    bot_thread = None

    if bot.work_model == 'bb':
        bot.is_active = True
        bot.save()
        bot_thread = threading.Thread(target=bb_worker, args=(bot,), name=f'BotThread_{bot.id}')

    if bot_thread is not None:
        bot_thread.start()

    return redirect(request.META.get('HTTP_REFERER'))
