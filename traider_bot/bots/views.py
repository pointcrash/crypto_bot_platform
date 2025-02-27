import logging
import threading
import time

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.bb.logic.start_logic import bb_worker
from bots.grid.logic.start_logic import grid_worker
from bots.models import BotModel
from bots.terminate_bot_logic import terminate_bot, terminate_bot_with_cancel_orders, \
    terminate_bot_with_cancel_orders_and_drop_positions
from bots.zinger.logic_market.start_logic import zinger_worker_market
from main.forms import AccountSelectForm
from orders.models import Position

logger = logging.getLogger('django')


@login_required
def bot_list(request):
    user = request.user
    position_qty_list = list()
    position_pnl_list = list()
    position_amount_list = list()

    if user.is_superuser:
        bots = BotModel.objects.all().select_related('bb').order_by('pk')
    else:
        bots = BotModel.objects.filter(owner=user).select_related('bb').order_by('pk')

    if request.method == 'POST':
        account_select_form = AccountSelectForm(request.POST, user=request.user)
        if account_select_form.is_valid():
            selected_account = account_select_form.cleaned_data['account']
            logger.info(f'{user} отсортировал список ботов по {selected_account}')
            if selected_account:
                bots = bots.filter(account=selected_account)
    else:
        logger.info(f'{user} открыл список ботов')
        account_select_form = AccountSelectForm(user=request.user)

    for bot in bots:
        lp = Position.objects.filter(account=bot.account, symbol_name=bot.symbol.name, side='LONG').last()
        sp = Position.objects.filter(account=bot.account, symbol_name=bot.symbol.name, side='SHORT').last()

        if lp:
            lp.unrealised_pnl = round(float(lp.unrealised_pnl), 2)
        if sp:
            sp.unrealised_pnl = round(float(sp.unrealised_pnl), 2)

        if lp and sp:
            position_qty_list.append((lp.qty, sp.qty))
            position_pnl_list.append((lp.unrealised_pnl, sp.unrealised_pnl))
            position_amount_list.append((round(float(lp.qty)*float(lp.entry_price), 2), round(float(sp.qty)*float(sp.entry_price), 2)))

        elif not lp and not sp:
            position_qty_list.append(('0', '0'))
            position_pnl_list.append(('0', '0'))
            position_amount_list.append(('0', '0'))

        elif not lp:
            position_qty_list.append(('0', sp.qty))
            position_pnl_list.append(('0', sp.unrealised_pnl))
            position_amount_list.append(('0', round(float(sp.qty)*float(sp.entry_price), 2)))

        elif not sp:
            position_qty_list.append((lp.qty, '0'))
            position_pnl_list.append((lp.unrealised_pnl, '0'))
            position_amount_list.append((round(float(lp.qty)*float(lp.entry_price), 2), '0'))

    bots = zip(bots, position_amount_list, position_pnl_list)

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
    user = request.user
    logger.info(
        f'{user} остановил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}. Event number-{event_number}')

    if event_number == 1:
        terminate_bot(bot, user)
    elif event_number == 2:
        terminate_bot_with_cancel_orders(bot, user)
    elif event_number == 3:
        terminate_bot_with_cancel_orders_and_drop_positions(bot, user)

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def delete_bot(request, bot_id, event_number):
    bot = BotModel.objects.get(pk=bot_id)
    user = request.user
    logger.info(
        f'{user} удалил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}. Event number-{event_number}')

    if event_number == 1:
        terminate_bot(bot, user)
    elif event_number == 2:
        terminate_bot_with_cancel_orders(bot, user)
    elif event_number == 3:
        terminate_bot_with_cancel_orders_and_drop_positions(bot, user)

    bot.delete()

    return redirect('bot_list')


@login_required
def bot_start(request, bot_id):
    bot = BotModel.objects.get(pk=bot_id)
    bot_thread = None
    user = request.user
    logger.info(
        f'{user} запустил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}')

    if bot.work_model == 'bb':
        bot.is_active = True
        bot.save()
        bot_thread = threading.Thread(target=bb_worker, args=(bot,), name=f'BotThread_{bot.id}')

    if bot.work_model == 'grid':
        bot.is_active = True
        bot.save()
        bot_thread = threading.Thread(target=grid_worker, args=(bot,), name=f'BotThread_{bot.id}')

    elif bot.work_model == 'zinger':
        bot.is_active = True
        bot.save()
        bot_thread = threading.Thread(target=zinger_worker_market, args=(bot,), name=f'BotThread_{bot.id}')
        # bot_thread = threading.Thread(target=zinger_worker, args=(bot,), name=f'BotThread_{bot.id}')

    if bot_thread is not None:
        bot_thread.start()

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def deactivate_all_my_bots(request):
    user = request.user
    BotModel.objects.filter(owner=user, is_active=True).update(is_active=False)
    time.sleep(3)

    return redirect(request.META.get('HTTP_REFERER'))
