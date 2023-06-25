import math
import multiprocessing
from django.shortcuts import render, redirect
import psutil
from bots.bot_logic import set_takes
from .forms import BotForm
from .models import Bot


def create_bot(request):
    if request.method == 'POST':
        form = BotForm(request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            bot.save()
            bot_process = multiprocessing.Process(target=set_takes, args=(bot, 3))
            bot_process.start()
            bot.process_id = str(bot_process.pid)
            bot.save()

            return redirect('bots_list')
    else:
        form = BotForm()

    return render(request, 'create_bot.html', {'form': form})


def bots_list(request):
    bots = Bot.objects.all()
    is_alive_list = []
    for bot in bots:
        if bot.process_id is not None:
            try:
                process = psutil.Process(int(bot.process_id))
                if process.is_running():
                    is_alive_list.append("Выполняется")
                else:
                    is_alive_list.append("Завершен")
            except psutil.NoSuchProcess:
                is_alive_list.append("Не найден")

        else:
            is_alive_list.append(None)

    bots = zip(bots, is_alive_list)
    return render(request, 'bots_list.html', {'bots': bots})


def bot_detail(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        form = BotForm(request.POST, instance=bot)  # Передаем экземпляр модели в форму
        if form.is_valid():
            form.save()
            return redirect('bots_list')
    else:
        form = BotForm(instance=bot)  # Передаем экземпляр модели в форму

    return render(request, 'bot_detail.html', {'form': form, 'bot': bot})


def start_bot(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    if bot.process_id is not None:
        bot_process = multiprocessing.Process(int(bot.process_id))
        bot_process.start()
    return redirect('bots_list')


def terminate_bot(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    if bot.process_id is not None:
        bot_process = multiprocessing.Process(int(bot.process_id))
        bot_process.terminate()
    return redirect('bots_list')
