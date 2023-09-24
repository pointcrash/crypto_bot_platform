import threading
from django.db import connections
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.SimpleHedge.logic.work import work_simple_hedge_bot
from bots.forms import BotForm, SimpleHedgeForm
from single_bot.logic.global_variables import lock, global_list_threads


@login_required
def simple_hedge_bot_create(request):
    title = 'Create Simple Hedge Bot'

    if request.method == 'POST':
        bot_form = BotForm(request=request, data=request.POST)
        simple_hedge_form = SimpleHedgeForm(data=request.POST)

        if bot_form.is_valid() and simple_hedge_form.is_valid():
            bot = bot_form.save(commit=False)
            bot.work_model = 'SmpHg'
            bot.owner = request.user
            bot.category = 'inverse'
            bot.save()

            simple_hedge = simple_hedge_form.save(commit=False)
            simple_hedge.bot = bot
            simple_hedge.save()

            connections.close_all()

            bot_thread = threading.Thread(target=work_simple_hedge_bot, args=(bot, simple_hedge))
            bot_thread.start()

            lock.acquire()
            global_list_threads[bot.pk] = bot_thread
            if lock.locked():
                lock.release()

            return redirect('single_bot_list')
    else:
        bot_form = BotForm(request=request)
        simple_hedge_form = SimpleHedgeForm()

    return render(request, 'simple_hedge/create.html',
                  {'form': bot_form, 'simple_hedge_form': simple_hedge_form, 'title': title, })
