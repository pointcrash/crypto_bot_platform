from rest_framework import viewsets, status
from rest_framework.response import Response

from bots.serializers import *


class BotModelViewSet(viewsets.ModelViewSet):
    queryset = BotModel.objects.all()
    serializer_class = BotModelSerializer

    def list_by_account(self, request, account_id=None):
        bots = BotModel.objects.filter(account=account_id)
        serializer = self.get_serializer(bots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BotLogsViewSet(viewsets.ModelViewSet):
    serializer_class = BotLogsSerializer

    def get_queryset(self):
        bot_id = self.kwargs.get('bot_id')
        queryset = Log.objects.filter(bot=bot_id)
        return queryset


class UserBotLogViewSet(viewsets.ModelViewSet):
    serializer_class = UserBotLogSerializer

    def get_queryset(self):
        bot_id = self.kwargs.get('bot_id')
        queryset = UserBotLog.objects.filter(bot=bot_id)
        return queryset
