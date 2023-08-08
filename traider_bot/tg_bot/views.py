from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from tg_bot.connect_tg_bot import get_chat_id
from tg_bot.forms import TelegramAccountForm


@login_required
def create_account(request):
    if request.method == 'POST':
        form = TelegramAccountForm(request.POST)
        if form.is_valid():
            acc = form.save(commit=False)
            acc.owner = request.user
            acc.chat_id = get_chat_id(acc.username)
            form.save()

            return redirect('account_list')
    else:
        form = TelegramAccountForm()

    return render(request, 'account/create_account.html', {'form': form})