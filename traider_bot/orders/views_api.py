from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response

from bots.models import BotModel
from orders.models import Position
from orders.serializers import PositionSerializer


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer

    def list_by_bots(self, request):
        bots_id_list = request.query_params.getlist('bot', [])
        bots_list = BotModel.objects.filter(id__in=bots_id_list)
        positions = []

        for bot in bots_list:
            lp = Position.objects.filter(account=bot.account, symbol_name=bot.symbol.name, side='LONG').last()
            sp = Position.objects.filter(account=bot.account, symbol_name=bot.symbol.name, side='SHORT').last()
            if lp:
                positions.append(lp)
            if sp:
                positions.append(sp)

        serializer = self.get_serializer(positions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


def login_test(request):
    return render(request, 'login_test.html')
