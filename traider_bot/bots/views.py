from django.shortcuts import render, redirect

from orders.models import Order
from .forms import BotForm
from .models import Bot


def create_bot(request):
    if request.method == 'POST':
        form = BotForm(request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            qty, bot.price = bot.get_quantity_from_price(bot.qty)
            bot.save()

            order = Order.objects.create(
                bot=bot,
                category=bot.category,
                symbol=bot.symbol,
                side=bot.side,
                orderType=bot.orderType,
                qty=qty,
                # price=bot.price,
            )
            return redirect('bots_list')
    else:
        form = BotForm()

    return render(request, 'create_bot.html', {'form': form})


def bots_list(request):
    bots = Bot.objects.all()

    return render(request, 'bots_list.html', {'bots': bots})


def bot_detail(request, bot_id):
    bot = Bot.objects.get(pk=bot_id)
    if request.method == 'POST':
        form = BotForm(request.POST, instance=bot)  # Передаем экземпляр модели в форму
        if form.is_valid():
            form.save()
            return redirect('bots_list')
    else:
        form = BotForm(instance=bot)  # Передаем экземпляр модели в форму

    return render(request, 'bot_detail.html', {'form': form, 'bot': bot})

