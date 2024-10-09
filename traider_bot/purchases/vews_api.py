import uuid

import requests
from django.conf import settings
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import ServiceProduct, Purchase
from .serializers import ServiceProductSerializer, PurchaseSerializer



class ServiceProductViewSet(viewsets.ModelViewSet):
    queryset = ServiceProduct.objects.all()
    serializer_class = ServiceProductSerializer

    permission_classes = [IsAdminUser]


class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Purchase.objects.all()
        return Purchase.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


def create_invoice_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Пользователь не авторизован'}, status=401)

    if request.method == 'POST':
        url = 'https://api.cryptocloud.plus/v2/invoice/create'
        auth_token = settings.CRYPTOCLOUD_AUTH_TOKEN
        shop_id = settings.CRYPTOCLOUD_SHOP_ID
        order_id = uuid.uuid4().hex
        amount = request.POST.get('amount')
        email = request.POST.get('email')

        if not amount or not email:
            return JsonResponse({'success': False, 'message': 'Не переданы обязательные параметры'}, status=400)

        data = {
            'shop_id': shop_id,
            'amount': amount,
            'currency': 'USD',
            'email': email,
            'order_id': order_id,
        }

        headers = {
            'Authorization': f'Token {auth_token}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=data, headers=headers)
        try:
            response_data = response.json()

            if response.status_code == 200 and 'result' in response_data:
                return JsonResponse({'success': True, 'link': response_data['result']['link']})
            else:
                return JsonResponse(
                    {'success': False, 'message': response_data.get('message', 'Ошибка при создании счета')},
                    status=response.status_code)

        except ValueError:
            return JsonResponse({'success': False, 'message': 'Некорректный ответ от API'}, status=500)

    else:
        return JsonResponse({'success': False, 'message': 'Неверный тип запроса (должен быть POST)'}, status=500)

