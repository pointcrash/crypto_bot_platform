import threading
import time

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.bb.logic.start_logic import bb_worker
from bots.bot_logic import func_get_symbol_list
from bots.forms import BotForm
from bots.models import Symbol, Bot
from bots.terminate_bot_logic import terminate_bot_with_cancel_orders


@login_required
def bb_bot_create(request):
    title = 'Create BB Bot'

    if request.method == 'POST':
        bot_form = BotForm(request=request, data=request.POST)

        if bot_form.is_valid():
            bot = bot_form.save(commit=False)
            bot.symbol = Symbol.objects.filter(name=bot.symbol.name, service=bot.account.service).first()
            bot.work_model = 'bb'
            bot.owner = request.user
            bot.category = 'linear'
            bot.is_active = True
            bot.save()

            bot_thread = threading.Thread(target=bb_worker, args=(bot,))
            bot_thread.start()

            return redirect('single_bot_list')
    else:
        bot_form = BotForm(request=request)

    return render(request, 'bb/create.html', {
        'form': bot_form,
        'title': title,
    })


@login_required
def bb_bot_edit(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        bot_form = BotForm(request.POST, request=request, instance=bot)
        if bot_form.is_valid():
            bot = bot_form.save(commit=False)
            if bot.is_active:
                terminate_bot_with_cancel_orders(bot)
                time.sleep(2)

            bot.is_active = True
            bot.save()
            bot_thread = threading.Thread(target=bb_worker, args=(bot,))
            bot_thread.start()
            return redirect('single_bot_list')
    else:
        bot_form = BotForm(request=request, instance=bot)

    return render(request, 'one_way/bb/bot_detail.html', {'form': bot_form, 'bot': bot})
