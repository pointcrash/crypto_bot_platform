import logging
import threading

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render, redirect

from bots.forms import BotModelForm, BotModelEditForm
from bots.models import Symbol, BotModel
from bots.terminate_bot_logic import terminate_bot
from bots.zinger.forms import ZingerForm
from bots.zinger.logic.start_logic import zinger_worker
from bots.zinger.logic_market.start_logic import zinger_worker_market

logger = logging.getLogger('django')


@login_required
def zinger_bot_create(request):
    title = 'Создание Zinger бота'
    user = request.user

    if request.method == 'POST':
        bot_form = BotModelForm(request=request, data=request.POST)
        zinger_form = ZingerForm(data=request.POST)

        if bot_form.is_valid() and zinger_form.is_valid():
            bot = bot_form.save(commit=False)
            bot.symbol = Symbol.objects.filter(name=bot.symbol.name, service=bot.account.service).first()
            bot.work_model = 'zinger'
            bot.owner = request.user
            bot.category = 'linear'
            bot.is_active = False
            bot.save()

            zinger_model = zinger_form.save(commit=False)
            zinger_model.bot = bot
            zinger_model.save()

            logger.info(
                f'{user} создал бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}')

            return redirect('bot_list')
    else:
        bot_form = BotModelForm(request=request)
        zinger_form = ZingerForm()

    return render(request, 'zinger/create.html', {
        'bot_form': bot_form,
        'zinger_form': zinger_form,
        'title': title,
    })


@login_required
def zinger_bot_edit(request, bot_id):
    bot = BotModel.objects.get(pk=bot_id)
    user = request.user

    symbol = bot.symbol
    account = bot.account
    if request.method == 'POST':
        bot_form = BotModelEditForm(request.POST, request=request, instance=bot)
        zinger_form = ZingerForm(request.POST, instance=bot.zinger)
        if bot_form.is_valid() and zinger_form.is_valid():
            if bot.is_active:
                bot.account = account
                bot.symbol = symbol
                terminate_bot(bot)

            zinger_model = zinger_form.save(commit=False)
            bot = bot_form.save(commit=False)
            bot.is_active = True
            bot.account = account
            bot.symbol = symbol
            zinger_model.save()
            bot.save()

            bot_thread = threading.Thread(target=zinger_worker_market, args=(bot,), name=f'BotThread_{bot.id}')
            bot_thread.start()
            logger.info(
                f'{user} отредактировал бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}')

            return redirect('bot_list')
    else:
        bot_form = BotModelForm(request=request, instance=bot)
        zinger_form = ZingerForm(instance=bot.zinger)

    bot_cache_keys = [key for key in cache.keys(f'bot{bot.id}*')]
    bot_cached_data = dict()
    for key in bot_cache_keys:
        new_key = key.split('_')[1]
        bot_cached_data[new_key] = cache.get(key)

    return render(request, 'zinger/edit.html', {
        'bot_form': bot_form,
        'zinger_form': zinger_form,
        'bot': bot,
        'symbol': symbol,
        'account': account,
        'bot_cached_data': bot_cached_data,
    })
