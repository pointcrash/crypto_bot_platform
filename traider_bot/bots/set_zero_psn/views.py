import threading
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from api_v5 import get_list
from bots.models import Symbol, Bot
from bots.set_zero_psn.logic.create_bot_obj import create_set0osn_bot_obj
from bots.set_zero_psn.logic.stop import stopping_set_zero_psn_bot
from bots.set_zero_psn.logic.work import work_set_zero_psn_bot
from bots.terminate_bot_logic import stop_bot_with_cancel_orders, terminate_thread
from main.models import Account
from main.psn_count import psn_count
from single_bot.logic.global_variables import lock, global_list_threads


@login_required
def start_set_zero_psn_bot(request, acc_id, symbol_name, trend):
    user = request.user
    account = Account.objects.filter(pk=acc_id).first()
    symbol = Symbol.objects.filter(name=symbol_name).first()

    symbol_list = get_list(account, symbol=symbol)
    psn = symbol_list[0] if symbol_list[0]['size'] != '0.0' else symbol_list[1]
    count_dict = psn_count(psn, int(symbol.priceScale))[str(trend)]

    bot = Bot.objects.filter(account=account, symbol=symbol).first()  # Add validation bot
    if bot:
        stop_bot_with_cancel_orders(bot)
        bot.delete()

    bot = create_set0osn_bot_obj(user, account, symbol, psn, count_dict)
    bot_thread = threading.Thread(target=work_set_zero_psn_bot, args=(bot, Decimal(psn['markPrice']), count_dict))
    bot_thread.start()

    lock.acquire()
    global_list_threads[bot.pk] = bot_thread
    if lock.locked():
        lock.release()

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def stop_set_zero_psn_bot(request, acc_id, symbol_name):
    account = Account.objects.filter(pk=acc_id).first()
    symbol = Symbol.objects.filter(name=symbol_name).first()
    bot = Bot.objects.filter(account=account, symbol=symbol).first()  # Add validation bot

    stopping_set_zero_psn_bot(bot, account, symbol)
    terminate_thread(bot.pk)

    return redirect(request.META.get('HTTP_REFERER'))
