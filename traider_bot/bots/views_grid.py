import multiprocessing
from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from bots.terminate_bot_logic import terminate_process_by_pid, get_status_process
from .bot_logic import get_update_symbols, create_bb_and_avg_obj
from .forms import BotForm, GridBotForm
from .bot_logic_grid import set_takes_for_grid_bot
from .models import Bot
from django.contrib import messages


@login_required
def grid_bots_list(request):
    user = request.user
    if user.is_superuser:
        bots = Bot.objects.filter(work_model='grid')
    else:
        bots = Bot.objects.filter(owner=user, work_model='grid')
    is_alive_list = []
    for bot in bots:
        if bot.process_id is not None:
            is_alive_list.append(get_status_process(bot.process_id))
        else:
            is_alive_list.append(None)

    bots = zip(bots, is_alive_list)
    return render(request, 'grid_bots_list.html', {'bots': bots})


@login_required
def grid_create_bot(request):
    title = 'Grid Bot'
    if request.method == 'POST':
        form = GridBotForm(request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            bot.work_model = 'grid'
            bot.owner = request.user
            bot.save()

            bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot)

            connections.close_all()
            bot_process = multiprocessing.Process(target=set_takes_for_grid_bot, args=(bot, bb_obj, bb_avg_obj))
            bot_process.start()
            bot.process_id = str(bot_process.pid)
            bot.save()

            return redirect('grid_bots_list')
    else:
        form = GridBotForm()

    return render(request, 'create_bot.html', {'form': form, 'title': title})


@login_required
def grid_bot_detail(request, bot_id):
    message = []
    error_message = messages.get_messages(request)
    if error_message:
        message.append(error_message)
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        form = GridBotForm(request.POST, instance=bot)  # Передаем экземпляр модели в форму
        if form.is_valid():
            bot = form.save()
            if get_status_process(bot.process_id):
                terminate_process_by_pid(bot.process_id)
            bot_process = multiprocessing.Process(target=set_takes_for_grid_bot, args=(bot, ))
            bot_process.start()
            bot.process_id = str(bot_process.pid)
            bot.save()
            return redirect('grid_bots_list')
    else:
        form = GridBotForm(instance=bot)  # Передаем экземпляр модели в форму

    return render(request, 'bot_detail.html', {'form': form, 'bot': bot, 'message': message})


def get_update_symbols_set(request, bot_type):
    get_update_symbols()
    if bot_type == 'grid':
        return redirect('grid_create_bot')
    else:
        return redirect('bb_create_bot')