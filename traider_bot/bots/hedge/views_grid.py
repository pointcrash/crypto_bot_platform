import multiprocessing
from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.hedge.grid_logic import set_takes_for_hedge_grid_bot
from bots.terminate_bot_logic import get_status_process, terminate_process_by_pid
from bots.forms import HedgeGridBotForm
from bots.models import Bot, Process
from django.contrib import messages


@login_required
def hedge_grid_bots_list(request):
    user = request.user
    bot_work_type = 'Grid'
    if user.is_superuser:
        bots = Bot.objects.filter(work_model='grid', category='inverse')
    else:
        bots = Bot.objects.filter(owner=user, work_model='grid', category='inverse')
    is_alive_list = []
    for bot in bots:
        pid = bot.process.pid
        is_alive_list.append(get_status_process(pid))

    bots = zip(bots, is_alive_list)
    return render(request, 'hedge/grid/bots_list.html', {'bots': bots, 'bot_work_type': bot_work_type, })


@login_required
def hedge_grid_create_bot(request):
    title = 'Hedge Grid Bot'

    if request.method == 'POST':
        form = HedgeGridBotForm(request=request, data=request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            bot.work_model = 'grid'
            bot.owner = request.user
            bot.category = 'inverse'
            bot.orderType = 'Market'
            bot.save()

            connections.close_all()
            bot_process = multiprocessing.Process(target=set_takes_for_hedge_grid_bot, args=(bot, ))
            bot_process.start()
            Process.objects.create(pid=str(bot_process.pid), bot=bot)

            return redirect('hedge_grid_list')
    else:
        form = HedgeGridBotForm(request=request)

    return render(request, 'hedge/grid/bot_create.html', {'form': form, 'title': title})


@login_required
def hedge_grid_bot_detail(request, bot_id):
    message = []
    error_message = messages.get_messages(request)
    if error_message:
        message.append(error_message)
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        form = HedgeGridBotForm(request.POST, instance=bot)  # Передаем экземпляр модели в форму
        if form.is_valid():
            bot = form.save()
            if get_status_process(bot.process.pid):
                terminate_process_by_pid(bot.process.pid)
            bot_process = multiprocessing.Process(target=set_takes_for_hedge_grid_bot, args=(bot,))
            bot_process.start()
            bot.process.pid = str(bot_process.pid)
            bot.process.save()
            return redirect('hedge_grid_list')
    else:
        form = HedgeGridBotForm(request=request, instance=bot)  # Передаем экземпляр модели в форму

    return render(request, 'hedge/grid/bots_detail.html', {'form': form, 'bot': bot, 'message': message})
