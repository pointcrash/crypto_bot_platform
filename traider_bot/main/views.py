from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import JsonResponse
import re
from datetime import datetime, timedelta

from api_v5 import get_query_account_coins_balance
from bots.models import Log, Bot
from timezone.forms import TimeZoneForm
from timezone.models import TimeZone
from .forms import RegistrationForm, LoginForm
from django.contrib.auth import authenticate, login, logout
from main.forms import AccountForm
from main.models import Account


def view_home(request):
    return render(request, 'home.html')


@login_required
def logs_list(request, bot_id):
    log_list = []
    bot = Bot.objects.get(id=bot_id)
    logs = Log.objects.filter(bot=bot_id).order_by('pk')
    user = request.user
    # gmt = 0
    # time_zone = None

    if request.method == 'POST':
        timezone_form = TimeZoneForm(request.POST)
        if timezone_form.is_valid():
            user_tz = TimeZone.objects.filter(users=user)
            for tz in user_tz:
                tz.users.remove(user)
            time_zone = timezone_form.cleaned_data['time_zone']
            time_zone.users.add(user)
            # gmt = int(time_zone.gmtOffset)
    else:
        # time_zone = TimeZone.objects.filter(users=user).first()
        timezone_form = TimeZoneForm()

    # if time_zone:
    #     for i in range(2):
    #         pattern = r'\d{2}:\d{2}:\d{2} \d{4}-\d{2}-\d{2}'
    #         for log in logs:
    #             content = log.content
    #             time = re.search(pattern, content)
    #             if time:
    #                 matched_text = time.group()
    #                 datetime_obj = datetime.strptime(matched_text, '%H:%M:%S %Y-%m-%d')
    #
    #                 if gmt < 0:
    #                     new_datetime = datetime_obj - timedelta(seconds=gmt)
    #                 else:
    #                     new_datetime = datetime_obj + timedelta(seconds=gmt)
    #
    #                 in_time = f'{new_datetime.time()} {new_datetime.date()}'
    #                 modified_content = re.sub(pattern, in_time, content)
    #                 log.content = modified_content
    #         Log.objects.bulk_update(logs, ['content'])

    for i in range(1, len(logs)+1):
        log_list.append([i, logs[i-1]])
    return render(request, 'logs.html', {'log_list': log_list, 'bot': bot, 'timezone_form': timezone_form})


@login_required
def view_logs_delete(request, bot_id):
    logs = Log.objects.filter(bot=bot_id)
    logs.delete()
    return redirect(request.META.get('HTTP_REFERER'))


def logs_view(request):
    user = request.user
    if user.is_superuser:
        bots = Bot.objects.all()
    else:
        bots = Bot.objects.filter(owner=user)
    return render(request, 'logs_detail.html', {'bots': bots})


@login_required
def account_list(request):
    user = request.user
    if user.is_superuser:
        accounts = Account.objects.all()
    else:
        accounts = Account.objects.filter(owner=request.user)
    return render(request, 'account/accounts_list.html', {'accounts': accounts, })


@login_required
def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            acc = form.save(commit=False)
            acc.owner = request.user
            form.save()

            return redirect('account_list')
    else:
        form = AccountForm()

    return render(request, 'account/create_account.html', {'form': form})


@login_required
def edit_account(request, acc_id):
    account = Account.objects.get(pk=acc_id)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            acc = form.save(commit=False)
            form.save()

            return redirect('account_list')
    else:
        form = AccountForm(instance=account)

    return render(request, 'account/account_edit.html', {'form': form})


@login_required
def delete_account(request, acc_id):
    acc = Account.objects.get(pk=acc_id)
    acc.delete()
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
    acc = Account.objects.get(pk=acc_id)
    balance = get_query_account_coins_balance(acc)[0]
    wb = balance['walletBalance']
    tb = balance['transferBalance']
    name = acc.name

    return JsonResponse({"wb": wb, "tb": tb, "name": name})

