import multiprocessing

from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.terminate_bot_logic import terminate_process_by_pid, get_status_process
from bots.bot_logic import create_bb_and_avg_obj, logging
from bots.bb_set_takes import set_takes
from bots.forms import BotForm
from bots.models import Bot, Process
from django.contrib import messages


@login_required
def one_way_bb_create_bot(request):
    title = 'Bollinger Bands Bot'

    if request.method == 'POST':
        form = BotForm(request=request, data=request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            bot.work_model = 'bb'
            bot.owner = request.user
            bot.category = 'linear'
            bot.save()
            bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot)
            connections.close_all()
            logging(bot, 'started work in')

            bot_process = multiprocessing.Process(target=set_takes, args=(bot, bb_obj, bb_avg_obj))
            bot_process.start()
            bot.process_id = str(bot_process.pid)
            bot.save()

            return redirect('one_way_bb_bots_list')
    else:
        form = BotForm(request=request)

    return render(request, 'one_way/create_bot.html', {'form': form, 'title': title, })


@login_required
def one_way_bb_bots_list(request):
    user = request.user
    if user.is_superuser:
        bots = Bot.objects.filter(work_model='bb', category='linear')
    else:
        bots = Bot.objects.filter(owner=user, work_model='bb', category='linear')
    is_alive_list = []
    for bot in bots:
        if bot.process_id is not None:
            is_alive_list.append(get_status_process(bot.process_id))
        else:
            is_alive_list.append(None)

    bots = zip(bots, is_alive_list)
    return render(request, 'one_way/bb/bb_bots_list.html', {'bots': bots})


@login_required
def one_way_bb_bot_detail(request, bot_id):
    message = []
    error_message = messages.get_messages(request)
    if error_message:
        message.append(error_message)
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        form = BotForm(request.POST, instance=bot)  # Передаем экземпляр модели в форму
        if form.is_valid():
            bot = form.save()
            if get_status_process(bot.process_id):
                terminate_process_by_pid(bot.process_id)
            bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot)
            bot_process = multiprocessing.Process(target=set_takes, args=(bot, bb_obj, bb_avg_obj))
            bot_process.start()
            bot.process_id = str(bot_process.pid)
            bot.save()
            return redirect('one_way_bb_bots_list')
    else:
        form = BotForm(request=request, instance=bot)  # Передаем экземпляр модели в форму

    return render(request, 'one_way/bb/bot_detail.html', {'form': form, 'bot': bot, 'message': message})






@login_required
def single_bb_bot_create(request):
    title = 'Create Bot'

    if request.method == 'POST':
        form = BotForm(request=request, data=request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            bot.work_model = 'bb'
            bot.owner = request.user
            bot.category = 'inverse'
            bot.save()

            connections.close_all()
            position_idx = 0 if bot.side == 'Buy' else 1
            bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot, position_idx)
            bot_process = multiprocessing.Process(target=set_takes, args=(bot, bb_obj, bb_avg_obj))
            bot_process.start()
            Process.objects.create(pid=str(bot_process.pid), bot=bot)
            return redirect('single_bot_list')
    else:
        form = BotForm(request=request)

    return render(request, 'one_way/create_bot.html', {'form': form, 'title': title, })