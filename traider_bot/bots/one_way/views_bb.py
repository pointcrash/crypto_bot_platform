import multiprocessing
import threading

from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.bot_logic import create_bb_and_avg_obj, clean_and_return_bot_object
from bots.bb_set_takes import set_takes
from bots.forms import BotForm
from bots.hedge.logic.work import set_takes_for_hedge_grid_bot
from bots.models import Bot
from django.contrib import messages

from bots.terminate_bot_logic import check_thread_alive, stop_bot_with_cancel_orders
from single_bot.logic.entry import get_position_idx_by_range
from single_bot.logic.global_variables import lock, global_list_threads
from single_bot.logic.work import get_position_idx


@login_required
def single_bb_bot_create(request):
    title = 'Create BB Bot'

    if request.method == 'POST':
        form = BotForm(request=request, data=request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            bot.work_model = 'bb'
            bot.owner = request.user
            bot.category = 'inverse'
            bot.save()

            connections.close_all()

            if bot.side == 'TS':
                bot_thread = threading.Thread(target=set_takes_for_hedge_grid_bot, args=(bot,))
            else:
                bot_thread = threading.Thread(target=set_takes, args=(bot,))
            bot_thread.start()

            lock.acquire()
            global_list_threads[bot.pk] = bot_thread
            lock.release()

            return redirect('single_bot_list')
    else:
        form = BotForm(request=request)

    return render(request, 'one_way/create_bot.html', {'form': form, 'title': title, })


@login_required
def single_bb_bot_detail(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        form = BotForm(request.POST, request=request, instance=bot)
        if form.is_valid():
            bot = form.save()
            new_bot = clean_and_return_bot_object(bot.pk)
            bot.delete()
            bot = new_bot
            bot.save()
            connections.close_all()

            if check_thread_alive(bot.pk):
                stop_bot_with_cancel_orders(bot)

            if bot.side == 'TS':
                bot_thread = threading.Thread(target=set_takes_for_hedge_grid_bot, args=(bot,))
            else:
                bot_thread = threading.Thread(target=set_takes, args=(bot,))
            bot_thread.start()

            lock.acquire()
            global_list_threads[bot.pk] = bot_thread
            lock.release()

            return redirect('single_bot_list')
    else:
        form = BotForm(request=request, instance=bot)  # Передаем экземпляр модели в форму

    return render(request, 'one_way/bb/bot_detail.html', {'form': form, 'bot': bot, })
