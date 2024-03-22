import threading

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.bb_set_takes import set_takes
from bots.bot_logic import custom_logging, clear_data_bot
from bots.hedge.logic.work import set_takes_for_hedge_grid_bot
from bots.models import Bot, SingleBot, IsTSStart
from bots.terminate_bot_logic import terminate_bot, terminate_bot_with_cancel_orders, \
    terminate_bot_with_cancel_orders_and_drop_positions
from single_bot.logic.global_variables import global_list_threads, lock
from single_bot.logic.work import bot_work_logic


def views_bots_type_choice(request, mode):
    user = request.user
    category = 'linear' if mode == 'one-way' else 'inverse'

    if user.is_superuser:
        grid_bots = Bot.objects.filter(work_model='grid', category=category)
    else:
        grid_bots = Bot.objects.filter(owner=user, work_model='grid', category=category)

    if user.is_superuser:
        bb_bots = Bot.objects.filter(work_model='bb', category=category)
    else:
        bb_bots = Bot.objects.filter(owner=user, work_model='bb', category=category)

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
    bot = Bot.objects.get(pk=bot_id)

    if event_number == 1:
        terminate_bot(bot)
    elif event_number == 2:
        terminate_bot_with_cancel_orders(bot)
    elif event_number == 3:
        terminate_bot_with_cancel_orders_and_drop_positions(bot)

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def delete_bot(request, bot_id, event_number):
    bot = Bot.objects.get(pk=bot_id)

    if event_number == 1:
        terminate_bot(bot)
    elif event_number == 2:
        terminate_bot_with_cancel_orders(bot)
    elif event_number == 3:
        terminate_bot_with_cancel_orders_and_drop_positions(bot)

    bot.delete()

    return redirect(request.META.get('HTTP_REFERER'))


def reboot_bots(request):
    bots = Bot.objects.all()
    for bot in bots:
        print(bot.is_active)
        if bot.is_active:
            bot_thread = None
            is_ts_start = IsTSStart.objects.filter(bot=bot)

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

            print(bot_thread)
            if bot_thread is not None:
                bot_thread.start()
                bot.is_active = True
                bot.save()
                lock.acquire()
                global_list_threads[bot.pk] = bot_thread
                if lock.locked():
                    lock.release()
    return redirect('single_bot_list')

