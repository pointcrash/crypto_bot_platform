import json

from django.shortcuts import render

from api_v5 import HTTP_Request
from orders.models import Order


def home(request):
    orders = Order.objects.all()
    return render(request, 'home.html', {'orders': orders})


# def orders():
#     order = Order.objects.get(pk=1)
#     endpoint = "/v5/order/create"
#     method = "POST"
#     params = {
#         'category': order.category,
#         'symbol': order.symbol,
#         'side': order.side,
#         'positionIdx': order.positionIdx,
#         'orderType': order.orderType,
#         'qty': str(order.qty),
#         'price': str(order.price),
#         'timeInForce': order.timeInForce,
#         'orderLinkId': order.orderLinkId
#     }
#     params = json.dumps(params)
#     try:
#         HTTP_Request(endpoint, method, params, "Create")
#     except Exception as e:
#         print("Error occurred:", str(e))
#
#
# orders()
