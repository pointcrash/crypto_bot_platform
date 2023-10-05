from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from tg_bot.connect_tg_bot import get_chat_id
from tg_bot.forms import TelegramAccountForm
from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message


@login_required
def telegram_list(request):
    user = request.user
    active_users = None
    status = False
    if user.is_superuser:
        active_users = TelegramAccount.objects.all()
    tg = TelegramAccount.objects.filter(owner=user).first()
    if tg:
        status = True
    return render(request, 'tg_list_users.html', context={'status': status, 'active_users': active_users, })


@login_required
def telegram_add_account(request):
    if request.method == 'POST':
        form = TelegramAccountForm(request.POST)
        if form.is_valid():
            try:
                acc = form.save(commit=False)
                acc.owner = request.user
                acc.chat_id = get_chat_id(acc.telegram_username)
                form.save()
            except Exception as e:
                if isinstance(e, ValueError):
                    error_messages = 'Имя пользователя не найдено. Напишите сообщение боту и проверьте правильность написания имени пользователя'
                else:
                    error_messages = str(e)
                return render(request, 'create_tg_account.html', {
                    'form': form,
                    'error_messages': error_messages
                })

            return redirect('telegram_list')
    else:
        form = TelegramAccountForm()

    return render(request, 'create_tg_account.html', {'form': form})


def delete_tg_acc(request):
    tg = TelegramAccount.objects.filter(owner=request.user).first()
    tg.delete()
    return redirect('telegram_list')


def say_hello(request):
    tg = TelegramAccount.objects.filter(owner=request.user).first()
    if tg:
        chat_id = tg.chat_id
        send_telegram_message(chat_id, message='Привет. Я бот-ассистент. Буду информировать тебя о работе твоих торговых ботов на сайте. ')
    return redirect('telegram_list')

