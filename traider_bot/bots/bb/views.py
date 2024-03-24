import threading
import time

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.bb.forms import BBForm
from bots.bb.logic.start_logic import bb_worker
from bots.bot_logic import func_get_symbol_list
from bots.forms import BotForm, BotModelForm
from bots.models import Symbol, Bot, BotModel
from bots.terminate_bot_logic import terminate_bot_with_cancel_orders, terminate_bot


@login_required
def bb_bot_create(request):
    title = 'Создание бота Боллинджера'

    if request.method == 'POST':
        bot_form = BotModelForm(request=request, data=request.POST)
        bb_form = BBForm(data=request.POST)

        print(bot_form.is_valid())
        print(bb_form.is_valid())
        print("Ошибка валидации формы бота:", bot_form.errors)
        print("Ошибка валидации формы bb:", bb_form.errors)
        print("Ошибка валидации формы bb:", bb_form.non_field_errors())

        if bot_form.is_valid() and bb_form.is_valid():
            bot = bot_form.save(commit=False)
            bot.symbol = Symbol.objects.filter(name=bot.symbol.name, service=bot.account.service).first()
            bot.work_model = 'bb'
            bot.owner = request.user
            bot.category = 'linear'
            bot.is_active = True
            bot.save()

            bb_model = bb_form.save(commit=False)
            bb_model.bot = bot
            bb_model.save()

            bot_thread = threading.Thread(target=bb_worker, args=(bot,))
            bot_thread.start()

            return redirect('single_bot_list')
    else:
        bot_form = BotModelForm(request=request)
        bb_form = BBForm()

    return render(request, 'bb/create.html', {
        'bot_form': bot_form,
        'bb_form': bb_form,
        'title': title,
    })


@login_required
def bb_bot_edit(request, bot_id):
    bot = BotModel.objects.get(pk=bot_id)
    if request.method == 'POST':
        bot_form = BotModelForm(request.POST, request=request, instance=bot)
        bb_form = BBForm(request.POST, instance=bot.bb)
        if bot_form.is_valid() and bb_form.is_valid():
            if bot.is_active:
                terminate_bot(bot)
                time.sleep(7)

            bb_model = bb_form.save(commit=False)
            bot = bot_form.save(commit=False)
            bot.is_active = True
            bb_model.save()
            bot.save()

            bot_thread = threading.Thread(target=bb_worker, args=(bot,))
            bot_thread.start()
            return redirect('single_bot_list')
    else:
        bot_form = BotModelForm(request=request, instance=bot)
        bb_form = BBForm(instance=bot.bb)

    return render(request, 'bb/edit.html', {'bot_form': bot_form, 'bb_form': bb_form, 'bot': bot})
