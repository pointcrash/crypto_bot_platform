import multiprocessing
from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.terminate_bot_logic import terminate_process_by_pid
from bots.bot_logic import get_update_symbols, create_bb_and_avg_obj
from bots.forms import GridBotForm
from bots.bot_logic_grid import set_takes_for_grid_bot
from bots.models import Bot, Process
from django.contrib import messages


@login_required
def one_way_grid_bots_list(request):

    user = request.user
    if user.is_superuser:
        bots = Bot.objects.filter(work_model='grid')
    else:
        bots = Bot.objects.filter(owner=user, work_model='grid')
    is_alive_list = []
    # for bot in bots:
    #     pid = bot.process.pid
    #     if pid is not None:
    #         is_alive_list.append(get_status_process(pid))
    #     else:
    #         is_alive_list.append(None)

    bots = zip(bots, is_alive_list)
    return render(request, 'one_way/grid/grid_bots_list.html', {'bots': bots, })


# @login_required
# def one_way_grid_create_bot(request):
#     title = 'Grid Bot'
#
#     if request.method == 'POST':
#         form = GridBotForm(request=request, data=request.POST)
#         if form.is_valid():
#             bot = form.save(commit=False)
#             bot.work_model = 'grid'
#             bot.owner = request.user
#             bot.category = 'linear'
#             bot.save()
#             bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot)
#
#             connections.close_all()
#             bot_process = multiprocessing.Process(target=set_takes_for_grid_bot, args=(bot, bb_obj, bb_avg_obj))
#             bot_process.start()
#             Process.objects.create(pid=str(bot_process.pid), bot=bot)
#             return redirect('one_way_grid_bots_list')
#     else:
#         form = GridBotForm(request=request)
#
#     return render(request, 'one_way/create_bot.html', {'form': form, 'title': title, })


@login_required
def one_way_grid_bot_detail(request, bot_id):
    message = []
    error_message = messages.get_messages(request)
    if error_message:
        message.append(error_message)
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        form = GridBotForm(request.POST, instance=bot)  # Передаем экземпляр модели в форму
        if form.is_valid():
            bot = form.save()
            # if get_status_process(bot.process.pid):
            #     terminate_process_by_pid(bot.process.pid)
            bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot)
            bot_process = multiprocessing.Process(target=set_takes_for_grid_bot, args=(bot, bb_obj, bb_avg_obj))
            bot_process.start()
            bot.process.pid = str(bot_process.pid)
            bot.process.save()
            return redirect('one_way_grid_bots_list')
    else:
        form = GridBotForm(request=request, instance=bot)  # Передаем экземпляр модели в форму

    return render(request, 'one_way/grid/bot_detail.html', {'form': form, 'bot': bot, 'message': message, })


def update_symbols_set(request):
    get_update_symbols()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def one_way_grid_create_bot(request):
    title = 'Grid Bot'

    if request.method == 'POST':
        form = GridBotForm(request=request, data=request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            bot.work_model = 'grid'
            bot.owner = request.user
            bot.category = 'inverse'
            bot.save()
            bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot)

            connections.close_all()
            bot_process = multiprocessing.Process(target=set_takes_for_grid_bot, args=(bot, bb_obj, bb_avg_obj))
            bot_process.start()
            Process.objects.create(pid=str(bot_process.pid), bot=bot)
            return redirect('one_way_grid_bots_list')
    else:
        form = GridBotForm(request=request)

    return render(request, 'one_way/create_bot.html', {'form': form, 'title': title, })