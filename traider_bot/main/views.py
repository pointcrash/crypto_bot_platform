from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bots.models import Log
from .forms import RegistrationForm, LoginForm
from django.contrib.auth import authenticate, login, logout
from main.forms import AccountForm
from main.models import Account


@login_required
def logs_list(request):
    logs = Log.objects.all()
    return render(request, 'logs.html', {'logs': logs})


@login_required
def account_list(request):
    accounts = Account.objects.all()
    return render(request, 'account/accounts_list.html', {'accounts': accounts})


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
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('bb_bots_list')
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
