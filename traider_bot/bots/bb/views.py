import logging
import threading
import time
from decimal import Decimal, ROUND_UP

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render, redirect

from api_2.api_aggregator import get_open_orders, get_position_inform, get_current_price, min_qty_check
from api_2.formattres import order_formatters
from bots.bb.forms import BBForm
from bots.bb.logic.start_logic import bb_worker
from bots.forms import BotModelForm, BotModelEditForm
from bots.general_functions import get_cur_positions_and_orders_info
from bots.models import Symbol, BotModel
from bots.terminate_bot_logic import terminate_bot
from orders.forms import OrderCustomForm

logger = logging.getLogger('django')


@login_required
def bb_bot_create(request):
    title = 'Создание бота Боллинджера'
    user = request.user

    if request.method == 'POST':
        bot_form = BotModelForm(request=request, data=request.POST)
        bb_form = BBForm(data=request.POST)

        if bot_form.is_valid() and bb_form.is_valid():
            bot = bot_form.save(commit=False)
            bot.symbol = Symbol.objects.filter(name=bot.symbol.name, service=bot.account.service).first()
            bot.work_model = 'bb'
            bot.owner = request.user
            bot.category = 'linear'
            bot.is_active = False
            bot.save()

            cur_price = Decimal(get_current_price(bot))
            qty_status = min_qty_check(bot.symbol, bot.leverage, cur_price, bot.amount_long)

            if qty_status:
                bb_model = bb_form.save(commit=False)
                bb_model.bot = bot
                bb_model.save()

                logger.info(
                    f'{user} создал бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}')

                return redirect('bot_list')

            else:
                min_amount = (Decimal(bot.symbol.minOrderQty) * cur_price / bot.leverage).quantize(Decimal(1), rounding=ROUND_UP)
                if not qty_status:
                    bot_form.add_error('amount_long', f'Инвестиция не может быть меньше {min_amount}$')
                bot.delete()
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
    bot_settings_template = 'bb/settings.html'
    bot = BotModel.objects.get(pk=bot_id)
    user = request.user

    symbol = bot.symbol
    account = bot.account
    if request.method == 'POST':
        bot_form = BotModelEditForm(request.POST, request=request, instance=bot)
        bb_form = BBForm(request.POST, instance=bot.bb)
        order_form = OrderCustomForm(request.POST)

        if bot_form.is_valid() and bb_form.is_valid():
            bot.account = account
            bot.symbol = symbol

            amount_long = Decimal(bot_form.cleaned_data.get('amount_long'))
            leverage = Decimal(bot_form.cleaned_data.get('leverage'))
            cur_price = Decimal(get_current_price(bot))
            qty_status = min_qty_check(bot.symbol, leverage, cur_price, amount_long)

            if qty_status:
                if bot.is_active:
                    restart_value = True
                    terminate_bot(bot)
                else:
                    restart_value = False

                bb_model = bb_form.save(commit=False)
                bot = bot_form.save(commit=False)
                bot.is_active = True
                bot.account = account
                bot.symbol = symbol
                bb_model.save()
                bot.save()

                if restart_value is True:
                    bot_thread = threading.Thread(target=bb_worker, args=(bot,), name=f'BotThread_{bot.id}')
                    bot_thread.start()
                logger.info(
                    f'{user} отредактировал бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}')

                return redirect('bot_list')

            else:
                min_amount = (Decimal(bot.symbol.minOrderQty) * cur_price / leverage).quantize(Decimal(1), rounding=ROUND_UP)
                if not qty_status:
                    bot_form.add_error('amount_long', f'Инвестиция не может быть меньше {min_amount}$')
    else:
        bot_form = BotModelForm(request=request, instance=bot)
        bb_form = BBForm(instance=bot.bb)
        order_form = OrderCustomForm()

    bot_cache_keys = [key for key in cache.keys(f'bot{bot.id}*')]
    bot_cached_data = dict()
    for key in bot_cache_keys:
        new_key = key.split('_')[1]
        bot_cached_data[new_key] = cache.get(key)

    positions, orders = get_cur_positions_and_orders_info(bot)

    return render(request, 'bots_info_page.html', {
        'bot_settings_template': bot_settings_template,
        'bot_form': bot_form,
        'bb_form': bb_form,
        'order_form': order_form,
        'bot': bot,
        'symbol': symbol,
        'account': account,
        'bot_cached_data': bot_cached_data,
        'orders': orders,
        'positions': positions,
    })
