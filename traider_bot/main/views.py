import datetime
import logging
import threading
import time
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from django.utils import timezone

from api_2.api_aggregator import get_futures_account_balance, internal_transfer, get_user_assets, withdraw, \
    get_pnl_by_time
from api_test.api_v5_bybit import get_query_account_coins_balance, get_list
from bots.bb.logic.start_logic import bb_worker
from bots.general_functions import all_symbols_update
from bots.models import Log, Symbol, BotModel
from bots.SetZeroPsn.logic.psn_count import psn_count
from bots.zinger.logic.start_logic import zinger_worker
from single_bot.logic.global_variables import global_list_bot_id
from timezone.forms import TimeZoneForm
from timezone.models import TimeZone
from .forms import RegistrationForm, LoginForm, DateRangeForm, InternalTransferForm, WithdrawForm, WhiteListAccountForm
from django.contrib.auth import authenticate, login, logout
from main.forms import AccountForm
from main.models import Account, WhiteListAccount
from .logic import calculate_pnl
import requests

logger = logging.getLogger('django')


def view_home(request):
    return render(request, 'home.html')


@login_required
def logs_list(request, bot_id):
    log_list = []
    bot = BotModel.objects.get(id=bot_id)
    logs = Log.objects.filter(bot=bot_id).order_by('pk')
    user = request.user
    not_timezone = False
    pnl = None

    if request.method == 'POST':
        timezone_form = TimeZoneForm(request.POST)
        date_form = DateRangeForm(request.POST)
        if date_form.is_valid():
            start_date = date_form.cleaned_data['start_date']
            end_date = date_form.cleaned_data['end_date']

            start_date = datetime.datetime.combine(start_date, datetime.time())
            end_date = datetime.datetime.combine(end_date, datetime.time())
            pnl = get_pnl_by_time(bot=bot, start_time=start_date, end_time=end_date)
            pnl = round(float(pnl), 2)
            not_timezone = True

        if not not_timezone:
            if timezone_form.is_valid():
                user_tz = TimeZone.objects.filter(users=user)
                for tz in user_tz:
                    tz.users.remove(user)
                time_zone = timezone_form.cleaned_data['time_zone']
                time_zone.users.add(user)
    else:
        date_form = DateRangeForm()
        timezone_form = TimeZoneForm()

        # if bot.time_update:
        #     pnl_list = calculate_pnl(bot=bot, start_date=bot.time_create, end_date=datetime.now())

    for i in range(1, len(logs) + 1):
        log_list.append([i, logs[i - 1]])

    log_list.sort(key=lambda x: x[0], reverse=True)
    logs_per_page = 50  # Количество логов на странице
    paginator = Paginator(log_list, logs_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    logger.info(f'{user} открыл логи бота ID: {bot_id}')
    return render(request, 'logs/logs.html', {
        'log_list': page_obj,
        'bot': bot,
        'timezone_form': timezone_form,
        'date_form': date_form,
        'calculated_bot_pnl_in_logs': pnl,
        # 'pnl_list': pnl_list,
    })


@login_required
def view_logs_delete(request, bot_id):
    user = request.user
    logs = Log.objects.filter(bot=bot_id)
    logs.delete()
    logger.info(f'{user} удалил логи бота ID: {bot_id}')
    return redirect(request.META.get('HTTP_REFERER'))


def logs_view(request):
    user = request.user
    if user.is_superuser:
        bots = BotModel.objects.all()
    else:
        bots = BotModel.objects.filter(owner=user)
    return render(request, 'logs_detail.html', {'bots': bots})


@login_required
def account_list(request):
    user = request.user
    if user.is_superuser:
        accounts = Account.objects.all()
    else:
        accounts = Account.objects.filter(owner=request.user)
    logger.info(f'{user} открыл список аккаунтов')

    internal_transfer_form = InternalTransferForm()
    return render(request, 'account/accounts_list.html',
                  {'accounts': accounts, 'internal_transfer_form': internal_transfer_form, })


@login_required
def account_position_list(request):
    bot_symbol_list = []
    name_symbol_set = set()
    if request.user.is_superuser:
        accounts = Account.objects.all()
    else:
        accounts = Account.objects.filter(owner=request.user)
    for account in accounts:
        positions_list = get_list(account)
        if positions_list:
            for psn in positions_list:
                symbol = Symbol.objects.filter(name=psn['symbol']).first()
                if symbol:
                    name_symbol_set.add(symbol.name)
                    count_dict = psn_count(psn, int(symbol.priceScale), symbol.tickSize)
                    bot = BotModel.objects.filter(account=account, symbol=symbol).first()
                    psn['positionBalance'] = str(round(Decimal(psn['positionBalance']), 2))
                    psn['unrealisedPnl'] = str(round(Decimal(psn['unrealisedPnl']), 2))
                    if bot:
                        if bot.work_model == 'set0psn' and bot.pk in global_list_bot_id:
                            set0psn = True
                        else:
                            set0psn = False
                        bot_symbol_list.append((account, bot.pk, psn, count_dict, set0psn))
                    else:
                        bot_symbol_list.append((account, '---', psn, count_dict, False))

    return render(request, 'positions/positions_list.html',
                  {'positions_list': bot_symbol_list, 'name_symbol_set': name_symbol_set})


@csrf_exempt
def recalculate_values(request):
    if request.method == 'POST':
        account_id = request.GET.get('accountId')
        symbol_name = request.GET.get('symbolName')
        trend = request.GET.get('trend')

        account = Account.objects.filter(pk=account_id).first()
        balance = get_query_account_coins_balance(account)[0]
        tb = Decimal(balance['transferBalance'])

        positions_list = get_list(account)
        for psn in positions_list:
            if psn['symbol'] == symbol_name:
                symbol = Symbol.objects.filter(name=psn['symbol']).first()
                count_dict = psn_count(psn, int(symbol.priceScale), symbol.tickSize)
                bot = BotModel.objects.filter(account=account, symbol=symbol).first()  # Add validation bot
                if tb > count_dict[trend]['margin'] * Decimal('1.1'):
                    enough_balance = True
                else:
                    enough_balance = False

                count_dict[trend]['tb'] = tb
                count_dict[trend]['enough_balance'] = enough_balance

        # Возвращение новых значений в формате JSON
        # print(count_dict[trend])
        return JsonResponse(count_dict[trend])

    return JsonResponse({'error': 'Invalid request method'})


@login_required
def create_account(request):
    user = request.user
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            acc = form.save(commit=False)
            acc.owner = request.user
            form.save()

            url = f"http://ws-manager:8008/ws/conn/new_account/{acc.pk}"
            requests.get(url)
            logger.info(f'{user} добавил новый аккаунт: {acc.pk} . {acc.name} . {acc.service.name}')
            return redirect('account_list')
    else:
        form = AccountForm()

    return render(request, 'account/create_account.html', {'form': form})


@login_required
def edit_account(request, acc_id):
    user = request.user
    account = Account.objects.get(pk=acc_id)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            acc = form.save(commit=False)
            form.save()

            url = f"http://ws-manager:8008/ws/conn/update_account/{acc.pk}"
            requests.get(url)

            logger.info(f'{user} отредактировал аккаунт: {account.pk} . {account.name} . {account.service.name}')
            return redirect('account_list')
    else:
        form = AccountForm(instance=account)

    return render(request, 'account/account_edit.html', {'form': form, 'account': account})


@login_required
def delete_account(request, acc_id):
    user = request.user
    acc = Account.objects.get(pk=acc_id)
    logger.info(f'{user} удалил аккаунт: {acc.pk} . {acc.name} . {acc.service.name}')
    acc.delete()

    url = f"http://ws-manager:8008/ws/conn/del_account/{acc_id}"
    requests.get(url)

    return redirect('account_list')


def registration_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Перенаправьте пользователя на страницу входа после успешной регистрации
    else:
        form = RegistrationForm()
    return render(request, 'registration.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required
def profile_list(request):
    user = request.user
    if user.is_superuser:
        users = User.objects.all().exclude(is_superuser=True)
    else:
        users = [user, ]
    return render(request, 'profile/profile_list.html', {'users': users})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_mode_switching(request, profile_id):
    if request.user.is_superuser:
        profile = User.objects.get(pk=profile_id)
        if profile.is_active:
            profile.is_active = False
        else:
            profile.is_active = True
        profile.save()
    return redirect(request.META.get('HTTP_REFERER'))


def get_balance(request, acc_id):
    account = Account.objects.get(pk=acc_id)
    try:
        balance = get_futures_account_balance(account)
        wb = balance['fullBalance']
        tb = balance['availableBalance']
    except Exception as e:
        wb = f'Ошибка получения баланса: {e}'
        tb = f'Ошибка получения баланса'
        print(e)
        print(f'Апи ключи аккаунта {account.name} устарели, замените')

    return JsonResponse({"wb": wb, "tb": tb, "name": account.name})


@login_required
def strategies_view(request):
    return render(request, 'strategies/strategies.html')


@login_required
def cleaning_logs_view(request):
    one_week_ago = timezone.now() - timedelta(weeks=1)
    logs = Log.objects.filter(bot=None, time_create__lt=one_week_ago)
    logs.delete()

    return render(request, 'strategies/strategies.html')


@login_required
def update_symbols(request):
    if request.user.is_superuser:
        all_symbols_update()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def restart_all_bots(request):
    active_bots = BotModel.objects.filter(is_active=True)
    bot_thread = None
    bot_id_list = []
    for bot in active_bots:
        bot_id_list.append(bot.id)
        bot.is_active = False
        bot.save()
    time.sleep(7)
    for bot_id in bot_id_list:
        bot = BotModel.objects.get(id=bot_id)
        bot.is_active = True
        bot.save()

        if bot.work_model == 'bb':
            bot_thread = threading.Thread(target=bb_worker, args=(bot,), name=f'BotThread_{bot.id}')

        elif bot.work_model == 'zinger':
            bot_thread = threading.Thread(target=zinger_worker, args=(bot,), name=f'BotThread_{bot.id}')

        if bot_thread is not None:
            bot_thread.start()

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def internal_transfer_view(request, acc_id):
    account = Account.objects.get(pk=acc_id)

    if request.method == 'POST':
        form = InternalTransferForm(request.POST)
        if form.is_valid():
            from_account_type = form.cleaned_data['fromAccountType']
            to_account_type = form.cleaned_data['toAccountType']
            symbol = form.cleaned_data['symbol']
            amount = form.cleaned_data['amount']
            internal_transfer(account=account, symbol=symbol, amount=amount, from_account_type=from_account_type,
                              to_account_type=to_account_type)

            return redirect('account_list')
    else:
        form = InternalTransferForm()

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def withdraw_view(request, acc_id):
    user = request.user
    account = Account.objects.get(pk=acc_id)
    futures_balance = get_futures_account_balance(account)['availableBalance']
    fund_balance = get_user_assets(account, symbol="USDT")

    user_accounts = Account.objects.filter(owner=user).exclude(id=acc_id)
    user_accounts =user_accounts.exclude(address=None).exclude(address='')
    whitelist = WhiteListAccount.objects.filter(user=user)

    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            chain = form.cleaned_data['chain']
            symbol = form.cleaned_data['symbol']
            amount = form.cleaned_data['qty']
            address = request.POST.get('address')

            response = withdraw(account=account, symbol=symbol, amount=amount, chain=chain, address=address)

            return redirect('account_list')
    else:
        form = WithdrawForm()

    return render(request, 'account/withdraw.html', context={
        'form': form,
        'futures_balance': futures_balance,
        'fund_balance': fund_balance,
        'account': account,
        'user_accounts': user_accounts,
        'whitelist': whitelist,
    })


@login_required
def whitelist_view(request):
    user = request.user
    whitelist = user.whitelist.all()

    if request.method == 'POST':
        form = WhiteListAccountForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = user
            address.symbol = 'USDT'
            address.chain = 'TRX'
            address.save()

            return redirect(request.META.get('HTTP_REFERER'))
    else:
        form = WhiteListAccountForm()

    return render(request, 'account/whitelist.html', context={
        'form': form,
        'whitelist': whitelist,
    })


@login_required
def get_account_assets_view(request, acc_id):
    account = Account.objects.get(pk=acc_id)

    futures_balance = get_futures_account_balance(account)
    futures_balance = futures_balance['availableBalance']

    fund_balance = get_user_assets(account, symbol="USDT")

    return JsonResponse({"futures_balance": futures_balance, "fund_balance": fund_balance})
