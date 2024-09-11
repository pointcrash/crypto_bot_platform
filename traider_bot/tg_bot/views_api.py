from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message
from tg_bot.serializers import TelegramAccountSerializer


class TelegramAccountViewSet(viewsets.ModelViewSet):
    serializer_class = TelegramAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return TelegramAccount.objects.filter(owner=user)

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


class TelegramAccountDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        try:
            tg = TelegramAccount.objects.filter(owner=user).first()

            if tg:
                tg.delete()
                return JsonResponse({'success': True, 'message': 'Telegram account was deleted successfully'},
                                    status=200)
            else:
                return JsonResponse({'success': False, 'message': 'Telegram account not found for this user'},
                                    status=404)

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class BotConnectView(APIView):
    def post(self, request):
        try:
            user_id = request.data['user_id']
            chat_id = request.data['chat_id']
            tg_username = request.data['username']
            user = User.objects.get_or_404(id=user_id)

            TelegramAccount.objects.create(owner=user, chat_id=chat_id, telegram_username=tg_username)

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
