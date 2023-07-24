import multiprocessing
from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.bb_set_takes import set_takes
from bots.hedge.grid_logic import set_takes_for_hedge_grid_bot
from bots.terminate_bot_logic import terminate_process_by_pid, get_status_process
from bots.bot_logic import get_update_symbols, create_bb_and_avg_obj
from bots.forms import GridBotForm
from bots.bot_logic_grid import set_takes_for_grid_bot
from bots.models import Bot, Process
from django.contrib import messages

from single_bot.logic.work import bot_work_logic


@login_required
def single_bot_list(request):
    user = request.user
    if user.is_superuser:
        bots = Bot.objects.filter()
    else:
        bots = Bot.objects.filter(owner=user)
    is_alive_list = []
    for bot in bots:
        pid = bot.process.pid
        if pid is not None:
            is_alive_list.append(get_status_process(pid))
        else:
            is_alive_list.append(None)

    bots = zip(bots, is_alive_list)
    return render(request, 'bot_list.html', {'bots': bots, })


@login_required
def single_bot_create(request):
    title = 'Create Bot'

    if request.method == 'POST':
        form = GridBotForm(request=request, data=request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            if form.cleaned_data['orderType'] == 'Limit':
                bot.work_model = 'bb'
            else:
                bot.work_model = 'grid'
            bot.owner = request.user
            bot.category = 'inverse'
            bot.save()

            connections.close_all()
            if bot.side == 'TS':
                bot_process = multiprocessing.Process(target=set_takes_for_hedge_grid_bot, args=(bot,))
            elif bot.work_model == 'bb':
                position_idx = 0 if bot.side == 'Buy' else 1
                bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot, position_idx)
                bot_process = multiprocessing.Process(target=set_takes, args=(bot, bb_obj, bb_avg_obj))
            else:
                bot_process = multiprocessing.Process(target=bot_work_logic, args=(bot,))
            bot_process.start()
            Process.objects.create(pid=str(bot_process.pid), bot=bot)
            return redirect('single_bot_list')
    else:
        form = GridBotForm(request=request)

    return render(request, 'one_way/create_bot.html', {'form': form, 'title': title, })


@login_required
def single_bot_detail(request, bot_id):
    message = []
    error_message = messages.get_messages(request)
    if error_message:
        message.append(error_message)
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        form = GridBotForm(request.POST, instance=bot)  # Передаем экземпляр модели в форму
        if form.is_valid():
            bot = form.save()
            if get_status_process(bot.process.pid):
                terminate_process_by_pid(bot.process.pid)
            bot_process = multiprocessing.Process(target=bot_work_logic, args=(bot,))
            bot_process.start()
            bot.process.pid = str(bot_process.pid)
            bot.process.save()
            return redirect('single_bot_list')
    else:
        form = GridBotForm(request=request, instance=bot)  # Передаем экземпляр модели в форму

    return render(request, 'one_way/grid/bot_detail.html', {'form': form, 'bot': bot, 'message': message, })


def bot_start(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    if bot.side == 'TS':
        bot_process = multiprocessing.Process(target=set_takes_for_hedge_grid_bot, args=(bot,))
    elif bot.work_model == 'bb':
        position_idx = 0 if bot.side == 'Buy' else 1
        bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot, position_idx)
        bot_process = multiprocessing.Process(target=set_takes, args=(bot, bb_obj, bb_avg_obj))
    else:
        bot_process = multiprocessing.Process(target=bot_work_logic, args=(bot,))
    bot_process.start()
    bot.process.pid = str(bot_process.pid)
    bot.process.save()
    return redirect('single_bot_list')


def update_symbols_set(request):
    get_update_symbols()
    return redirect(request.META.get('HTTP_REFERER'))
