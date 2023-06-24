import json

from django.shortcuts import render

from api_v5 import HTTP_Request
from orders.models import Order


def home(request):
    orders = Order.objects.all()
    return render(request, 'story_orders.html', {'orders': orders})