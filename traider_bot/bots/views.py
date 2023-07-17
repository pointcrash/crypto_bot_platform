from django.shortcuts import render, redirect

from bots.models import Bot


def views_bots_type_choice(request, mode):
    user = request.user
    category = 'linear' if mode == 'one-way' else 'inverse'

    if user.is_superuser:
        grid_bots = Bot.objects.filter(work_model='grid', category=category)
    else:
        grid_bots = Bot.objects.filter(owner=user, work_model='grid', category=category)

    if user.is_superuser:
        bb_bots = Bot.objects.filter(work_model='bb', category=category)
    else:
        bb_bots = Bot.objects.filter(owner=user, work_model='bb', category=category)

    if mode == 'hedge':
        title = 'Hedge Mode'
        return render(request, 'hedge/type_choice.html',
                      {'title': title, 'mode': mode, 'bb_bots': bb_bots, 'grid_bots': grid_bots, })
    elif mode == 'one-way':
        title = 'One-Way Mode'
        return render(request, 'one_way/type_choice.html',
                      {'title': title, 'mode': mode, 'bb_bots': bb_bots, 'grid_bots': grid_bots, })
    else:
        return redirect('/')

