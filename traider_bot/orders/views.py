from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from api_v5 import cancel_order
from bots.models import Bot
from orders.forms import OrderCreateForm
from orders.models import Order


@login_required
def create_order_view(request, bot_id):
    title = 'Create order'
    bot = Bot.objects.get(pk=bot_id)

    if request.method == 'POST':
        form = OrderCreateForm(data=request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.bot = bot
            order.category = 'inverse'
            order.symbol = bot.symbol.name
            order.orderType = 'Limit'
            order.save()

            return redirect('single_bot_list')
    else:
        form = OrderCreateForm()

    return render(request, 'create_order.html', {'title': title, 'form': form})


@login_required
def cancel_order_view(request, bot_id, order_id):
    bot = Bot.objects.get(pk=bot_id)
    order = Order.objects.filter(orderLinkId=order_id)

    cancel_order(bot, order_id)

    if order:
        order.delete()

    return redirect(request.META.get('HTTP_REFERER'))
