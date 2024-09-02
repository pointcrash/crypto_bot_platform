import logging
import threading
from decimal import Decimal, ROUND_UP

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.utils import timezone

from api_2.api_aggregator import get_current_price, place_conditional_order, place_order, get_position_inform, \
    get_quantity_from_price, min_qty_check
from bots.forms import BotModelForm, BotModelEditForm
from bots.general_functions import get_cur_positions_and_orders_info
from bots.models import Symbol, BotModel
from bots.terminate_bot_logic import terminate_bot
from bots.zinger.forms import ZingerForm, AverageZingerForm
from bots.zinger.logic_market.start_logic import zinger_worker_market
from orders.forms import OrderCustomForm
from orders.models import Position, Order

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

            cur_price = Decimal(get_current_price(bot))
            long_qty_status = min_qty_check(bot.symbol, bot.leverage, cur_price, bot.amount_long)
            short_qty_status = min_qty_check(bot.symbol, bot.leverage, cur_price, bot.amount_short)

            if long_qty_status and short_qty_status:
                zinger_model = zinger_form.save(commit=False)
                zinger_model.bot = bot
                zinger_model.save()

                logger.info(
                    f'{user} создал бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}')

                return redirect('bot_list')

            else:
                min_amount = (Decimal(bot.symbol.minOrderQty) * cur_price / bot.leverage).quantize(Decimal(1), rounding=ROUND_UP)
                if not long_qty_status:
                    bot_form.add_error('amount_short', f'Инвестиция не может быть меньше {min_amount}$')
                if not short_qty_status:
                    bot_form.add_error('amount_long', f'Инвестиция не может быть меньше {min_amount}$')
                bot.delete()

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
    bot_settings_template = 'zinger/settings.html'
    bot = BotModel.objects.get(pk=bot_id)
    user = request.user

    symbol = bot.symbol
    account = bot.account
    if request.method == 'POST':
        bot_form = BotModelEditForm(request.POST, request=request, instance=bot)
        zinger_form = ZingerForm(request.POST, instance=bot.zinger)
        order_form = OrderCustomForm(request.POST)
        average_form = AverageZingerForm(request.POST)

        if bot_form.is_valid() and zinger_form.is_valid():
            bot.account = account
            bot.symbol = symbol

            amount_long = Decimal(bot_form.cleaned_data.get('amount_long'))
            amount_short = Decimal(bot_form.cleaned_data.get('amount_short'))
            leverage = Decimal(bot_form.cleaned_data.get('leverage'))
            cur_price = Decimal(get_current_price(bot))
            long_qty_status = min_qty_check(bot.symbol, leverage, cur_price, amount_long)
            short_qty_status = min_qty_check(bot.symbol, leverage, cur_price, amount_short)

            if long_qty_status and short_qty_status:
                if bot.is_active:
                    restart_value = True
                    terminate_bot(bot)
                else:
                    restart_value = False

                zinger_model = zinger_form.save(commit=False)
                bot = bot_form.save(commit=False)
                bot.is_active = True if restart_value is True else False
                bot.account = account
                bot.symbol = symbol
                zinger_model.save()
                bot.save()

                if restart_value is True:
                    bot_thread = threading.Thread(target=zinger_worker_market, args=(bot,), name=f'BotThread_{bot.id}')
                    bot_thread.start()
                logger.info(
                    f'{user} отредактировал бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}')

                return redirect('bot_list')
            else:
                min_amount = (Decimal(bot.symbol.minOrderQty) * cur_price / leverage).quantize(Decimal(1), rounding=ROUND_UP)
                if not long_qty_status:
                    bot_form.add_error('amount_short', f'Инвестиция не может быть меньше {min_amount}$')
                if not short_qty_status:
                    bot_form.add_error('amount_long', f'Инвестиция не может быть меньше {min_amount}$')

    else:
        bot_form = BotModelForm(request=request, instance=bot)
        zinger_form = ZingerForm(instance=bot.zinger)
        order_form = OrderCustomForm()
        average_form = AverageZingerForm()

    bot_cache_keys = [key for key in cache.keys(f'bot{bot.id}*')]
    bot_cached_data = dict()
    for key in bot_cache_keys:
        new_key = key.split('_')[1]
        bot_cached_data[new_key] = cache.get(key)

    position_history = Position.objects.filter(account=bot.account, symbol_name=bot.symbol.name).order_by('-time_update')
    order_history = Order.objects.filter(account=bot.account, symbol_name=bot.symbol.name).order_by('-time_update')

    positions, orders = get_cur_positions_and_orders_info(bot)
    logger.info(
        f'{orders}')

    return render(request, 'bots_info_page.html', {
        'bot_settings_template': bot_settings_template,
        'bot_form': bot_form,
        'zinger_form': zinger_form,
        'order_form': order_form,
        'average_form': average_form,
        'bot': bot,
        'symbol': symbol,
        'account': account,
        'bot_cached_data': bot_cached_data,
        'positions': positions,
        'orders': orders,
        'order_history': order_history,
        'position_history': position_history,
    })


@login_required
def start_zinger_bot_view(request, bot_id, event_number):
    bot = BotModel.objects.get(pk=bot_id)
    user = request.user

    bot.is_active = True
    if event_number == 2:
        bot.time_create = timezone.now()
    bot.save()
    bot_thread = threading.Thread(target=zinger_worker_market, args=(bot,), name=f'BotThread_{bot.id}')

    if bot_thread is not None:
        bot_thread.start()

    logger.info(
        f'{user} запустил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}')

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def zinger_manual_average_view(request, bot_id):
    bot = BotModel.objects.get(pk=bot_id)

    if request.method == 'POST':
        form = AverageZingerForm(request.POST)
        if form.is_valid():
            qty = Decimal(form.cleaned_data['qty'])
            nominal = form.cleaned_data['price']
            price = Decimal(form.cleaned_data['price'])
            order_type = form.cleaned_data['type']
            form_psn_side = form.cleaned_data['psnSide']

            qty_list = dict()
            side_list = ['LONG', 'SHORT'] if form_psn_side == 'BOTH' else [form_psn_side]
            if nominal == '%':
                psn_data = get_position_inform(bot)
                for psn in psn_data:
                    qty_list[psn['side']] = abs(Decimal(psn['qty'])) * qty / 100

            elif nominal == '$':
                for side in ['LONG', 'SHORT']:
                    buy_qty = get_quantity_from_price(bot=bot, price=price, amount=qty)
                    qty_list[side] = buy_qty

            for psn_side in side_list:
                if order_type == 'MARKET':
                    side = 'BUY' if psn_side == 'LONG' else 'SHORT'
                    response = place_order(bot=bot, side=side, position_side=psn_side, qty=qty_list[psn_side],
                                           price=price, order_type=order_type)

                elif order_type == 'LIMIT':
                    cur_price = get_current_price(bot)
                    side = 'BUY' if psn_side == 'LONG' else 'SHORT'
                    trigger_direction = 1 if cur_price < price else 2
                    response = place_conditional_order(bot=bot, side=side, position_side=psn_side,
                                                       qty=qty_list[psn_side], trigger_price=price,
                                                       trigger_direction=trigger_direction)

            return redirect('zinger_bot_edit', bot_id=bot.id)
    else:
        form = AverageZingerForm()

    return render(request, 'create_order.html', {'form': form})
