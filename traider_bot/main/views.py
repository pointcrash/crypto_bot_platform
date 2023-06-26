import json

from django.shortcuts import render

from api_v5 import HTTP_Request
from main.models import Log
from orders.models import Order


def home(request):
    logs = Log.objects.all()
    return render(request, 'story_orders.html', {'logs': logs})


def logs_list(request):
    logs = Log.objects.all()
    return render(request, 'logs.html', {'logs': logs})

# def logs_list(request):
#     logs = Log.objects.all()
#     return render(request, 'logs.html', {'logs': logs})
