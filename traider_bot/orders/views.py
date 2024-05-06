from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from api_2.api_aggregator import cancel_order, get_current_price, place_conditional_order, place_order
from bots.models import BotModel
from orders.forms import OrderCustomForm


@login_required
def cancel_selected_order_view(request, bot_id, order_id):
    bot = BotModel.objects.get(pk=bot_id)
    cancel_order(bot, order_id)

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def place_custom_order_view(request, bot_id):
    bot = BotModel.objects.get(pk=bot_id)

    if request.method == 'POST':
        form = OrderCustomForm(request.POST)
        if form.is_valid():
            qty = Decimal(form.cleaned_data['qty'])
            # price = Decimal(form.cleaned_data['triggerPrice']) if form.cleaned_data['triggerPrice'] else None
            trigger_price = Decimal(form.cleaned_data['triggerPrice']) if form.cleaned_data['triggerPrice'] else None
            order_type = form.cleaned_data['type']
            side = form.cleaned_data['side']
            psn_side = form.cleaned_data['psnSide']

            if side == 'OPEN':
                if psn_side == 'LONG':
                    side = 'BUY'
                elif psn_side == 'SHORT':
                    side = 'SELL'

            elif side == 'CLOSE':
                if psn_side == 'LONG':
                    side = 'SELL'
                elif psn_side == 'SHORT':
                    side = 'BUY'

            if trigger_price and order_type == 'MARKET':
                cur_price = get_current_price(bot)
                trigger_direction = 1 if cur_price < trigger_price else 2
                response = place_conditional_order(bot=bot, side=side, position_side=psn_side, qty=qty,
                                                   trigger_price=trigger_price, trigger_direction=trigger_direction)
            else:
                response = place_order(bot=bot, side=side, position_side=psn_side, qty=qty, price=trigger_price,
                                       order_type=order_type)

            if bot.work_model == 'bb':
                return redirect('bb_bot_edit', bot_id=bot.id)
            elif bot.work_model == 'zinger':
                return redirect('zinger_bot_edit', bot_id=bot.id)
    else:
        form = OrderCustomForm()

    return render(request, 'create_order.html', {'form': form})


@login_required
def close_selected_position_view(request, bot_id, psn_side, qty):
    bot = BotModel.objects.get(pk=bot_id)
    side = 'SELL' if psn_side == 'LONG' else 'BUY'
    qty = abs(Decimal(qty))
    response = place_order(bot=bot, side=side, position_side=psn_side, qty=qty, price=None, order_type='MARKET')
    print(response)

    return redirect(request.META.get('HTTP_REFERER'))