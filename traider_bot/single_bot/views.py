from django.contrib.auth.decorators import login_required
from django.http import HttpResponse



@login_required
def single_bot_create(request):
    pass
    # title = 'Create Bot'
    #
    # if request.method == 'POST':
    #     bot_form = GridBotForm(request=request, data=request.POST)
    #     set0psn_form = Set0PsnForm(data=request.POST)
    #     opposite_psn_form = OppositePositionForm(data=request.POST)
    #
    #     if bot_form.is_valid() and set0psn_form.is_valid() and opposite_psn_form.is_valid():
    #         bot = bot_form.save(commit=False)
    #         bot.work_model = 'grid'
    #         bot.owner = request.user
    #         bot.category = 'linear'
    #         bot.save()
    #
    #         set0psn = set0psn_form.save(commit=False)
    #         set0psn.bot = bot
    #         set0psn.save()
    #
    #         opposite_psn = opposite_psn_form.save(commit=False)
    #         opposite_psn.bot = bot
    #         opposite_psn.save()
    #
    #         connections.close_all()
    #
    #         if bot.side == 'TS':
    #             bot_thread = threading.Thread(target=set_takes_for_hedge_grid_bot, args=(bot,))
    #         else:
    #             bot_thread = threading.Thread(target=bot_work_logic, args=(bot,))
    #         bot_thread.start()
    #         lock.acquire()
    #         global_list_threads[bot.pk] = bot_thread
    #         lock.release()
    #
    #         return redirect('bot_list')
    # else:
    #     bot_form = GridBotForm(request=request)
    #     set0psn_form = Set0PsnForm()
    #     opposite_psn_form = OppositePositionForm()
    #
    # return render(request, 'create_bot.html', {
    #     'form': bot_form,
    #     'title': title,
    #     'set0psn_form': set0psn_form,
    #     'opposite_psn_form': opposite_psn_form,
    # })


@login_required
def single_bot_detail(request, bot_id):
    pass
    # bot = BotModel.objects.get(pk=bot_id)
    # set0psn = Set0Psn.objects.filter(bot=bot).first()
    # opposite_psn = OppositePosition.objects.filter(bot=bot).first()
    # symbol_list = func_get_symbol_list(bot)
    # symbol_list = symbol_list[0] if float(symbol_list[0]['size']) > 0 else symbol_list[1]
    # symbol_list['avgPrice'] = round(float(symbol_list['avgPrice']), 2)
    # symbol_list['unrealisedPnl'] = round(float(symbol_list['unrealisedPnl']), 2)
    # symbol_list['positionBalance'] = round(float(symbol_list['positionBalance']), 2)
    # if request.method == 'POST':
    #     bot_form = GridBotForm(request.POST, request=request, instance=bot)
    #     if set0psn:
    #         set0psn_form = Set0PsnForm(data=request.POST, instance=set0psn)
    #     else:
    #         set0psn_form = Set0PsnForm(data=request.POST)
    #     if opposite_psn:
    #         opposite_psn_form = OppositePositionForm(data=request.POST, instance=opposite_psn)
    #     else:
    #         opposite_psn_form = OppositePositionForm(data=request.POST)
    #
    #     if bot_form.is_valid() and set0psn_form.is_valid():
    #         bot = bot_form.save(commit=False)
    #
    #         set0psn_form.save(commit=False)
    #         set0psn.bot = bot
    #         set0psn.save()
    #
    #         opposite_psn = opposite_psn_form.save(commit=False)
    #         opposite_psn.bot = bot
    #         opposite_psn.save()
    #
    #         if check_thread_alive(bot.pk):
    #             stop_bot_with_cancel_orders(bot)
    #
    #         if bot.side == 'TS':
    #             bot_thread = threading.Thread(target=set_takes_for_hedge_grid_bot, args=(bot,))
    #         else:
    #             bot_thread = threading.Thread(target=bot_work_logic, args=(bot,))
    #
    #         bot_thread.start()
    #         bot.is_active = True
    #         bot.save()
    #
    #         lock.acquire()
    #         global_list_threads[bot.pk] = bot_thread
    #         if lock.locked():
    #             lock.release()
    #
    #         return redirect('bot_list')
    # else:
    #     bot_form = GridBotForm(request=request, instance=bot)
    #     if set0psn:
    #         set0psn_form = Set0PsnForm(instance=set0psn)
    #     else:
    #         set0psn_form = Set0PsnForm()
    #     if opposite_psn:
    #         opposite_psn_form = OppositePositionForm(instance=opposite_psn)
    #     else:
    #         opposite_psn_form = OppositePositionForm()
    #
    # order_list_status, order_list = get_open_orders(bot)
    # for order in order_list:
    #     time = int(order['updatedTime'])
    #     dt_object = datetime.fromtimestamp(time / 1000.0)
    #     formatted_date = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    #     order['updatedTime'] = formatted_date
    #
    # return render(request, 'bot_detail.html', {'form': bot_form,
    #                                            'opposite_psn_form': opposite_psn_form,
    #                                            'set0psn_form': set0psn_form,
    #                                            'bot': bot,
    #                                            'symbol_list': symbol_list,
    #                                            'order_list': order_list
    #                                            })


def say_hello(request):
    return HttpResponse('<h1>Hello guys</h1>')
