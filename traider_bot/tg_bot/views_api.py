from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message
from tg_bot.serializers import TelegramAccountSerializer


class TelegramAccountViewSet(viewsets.ModelViewSet):
    queryset = TelegramAccount.objects.all()
    serializer_class = TelegramAccountSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TelegramSayHelloView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            tg = TelegramAccount.objects.filter(owner=user).first()

            if tg:
                chat_id = tg.chat_id
                send_telegram_message(
                    chat_id,
                    message='Привет. Я бот-ассистент. Буду информировать тебя о работе твоих торговых ботов на сайте.'
                )
                return JsonResponse({'success': True, 'message': 'Message was sent'}, status=200)
            else:
                return JsonResponse({'success': False, 'message': 'Telegram account not found for this user'},
                                    status=404)

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
