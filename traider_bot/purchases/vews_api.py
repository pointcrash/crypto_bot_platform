import json
import logging
import uuid

import jwt
import requests
from django.conf import settings
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView

from tariffs.models import UserTariff
from .models import ServiceProduct, Purchase
from .serializers import ServiceProductSerializer, PurchaseSerializer
from django.shortcuts import get_object_or_404


logger = logging.getLogger('debug_logger')


class ServiceProductViewSet(viewsets.ModelViewSet):
    queryset = ServiceProduct.objects.all()
    serializer_class = ServiceProductSerializer

    permission_classes = [IsAdminUser]


class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # if self.request.user.is_staff:
        #     return Purchase.objects.all()
        return Purchase.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CreateInvoiceView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        if request.method == 'POST':
            try:
                data = request.data
                email = data.get('email')
                product_id = int(data.get('product_id'))

            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)

            if not product_id or not email:
                return JsonResponse({'success': False, 'message': 'Не переданы обязательные параметры'}, status=400)

            url = 'https://api.cryptocloud.plus/v2/invoice/create'
            auth_token = settings.CRYPTOCLOUD_AUTH_TOKEN
            shop_id = settings.CRYPTOCLOUD_SHOP_ID
            order_id = uuid.uuid4().hex

            product = get_object_or_404(ServiceProduct, id=product_id)
            Purchase.objects.create(user=request.user, product=product, order_id=order_id)

            data = {
                'shop_id': shop_id,
                'amount': str(product.price.normalize()),
                'currency': 'USD',
                'email': email,
                'order_id': order_id,
            }

            headers = {
                'Authorization': f'Token {auth_token}',
                'Content-Type': 'application/json'
            }


            try:
                response = requests.post(url, json=data, headers=headers)
                response_data = response.json()

                if response.status_code == 200 and 'result' in response_data:
                    return JsonResponse({'success': True, 'link': response_data['result']['link']})
                else:
                    return JsonResponse(
                        {'success': False, 'message': response_data.get('message', 'Ошибка при создании счета')},
                        status=response.status_code)

            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Некорректный ответ от API', 'error': str(e)}, status=500)

        else:
            return JsonResponse({'success': False, 'message': 'Неверный тип запроса (должен быть POST)'}, status=500)


class PurchasesCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"ПОЛУЧЕНО СООБЩЕНИЕ ОБ ОПЛАТЕ: {request.POST.dict()}")
        status = request.POST.get('status')
        order_id = request.POST.get('order_id')
        token = request.POST.get('token')

        secret_key = settings.CRYPTOCLOUD_SECRET

        if status == 'success':
            if not order_id or not token:
                logger.error(f"Недостаточно данных в запросе: {request.POST.dict()}")
                return JsonResponse({'success': False, 'message': 'Не переданы необходимые параметры'}, status=400)

            try:
                decoded_token = jwt.decode(token, secret_key, algorithms=["HS256"])
                logger.error(f"Decoded token payload: {decoded_token}")
            except jwt.ExpiredSignatureError:
                logger.error(f"Token has expired {token}")
                return JsonResponse({'success': False, 'message': 'Token has expired'}, status=400)
            except jwt.InvalidTokenError:
                logger.error(f"Invalid token {token}")
                return JsonResponse({'success': False, 'message': 'Invalid token'}, status=400)

            purchase = Purchase.objects.filter(order_id=order_id).first()
            if purchase:
                try:
                    purchase.enrolled = True
                    purchase.save()

                    user = purchase.user
                    tariff = purchase.product.tariff
                    UserTariff.objects.create(user=user, tariff=tariff)

                    purchase.completed = True
                    purchase.save()

                    logger.info(f"Покупка была успешно оплачена: {order_id}")
                    return JsonResponse({'success': True, 'message': 'Покупка была успешно оплачена'}, status=200)

                except Exception as e:
                    logger.error(f"Ошибка обработки покупки {order_id}: {str(e)}")
                    return JsonResponse({'success': False, 'message': 'Ошибка обработки покупки'}, status=500)
            else:
                logger.error(f"Покупка с order_id {order_id} не найдена.")
                return JsonResponse({'success': False, 'message': 'Покупка не найдена'}, status=404)

        # Если статус не 'success'
        logger.error(f"Ошибка оплаты покупки с order_id {order_id}.")
        return JsonResponse({'success': False, 'message': f"Ошибка оплаты покупки с order_id {order_id}."}, status=400)


class PurchaseGuestTariffView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        status = request.POST.get('status')
        order_id = request.POST.get('order_id')
        token = request.POST.get('token')

        return JsonResponse({'success': False, 'message': f"Ошибка оплаты покупки с order_id {order_id}."}, status=400)





