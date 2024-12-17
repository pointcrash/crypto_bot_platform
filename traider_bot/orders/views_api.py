from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api_2.api_aggregator import cancel_order
from bots.models import BotModel
from orders.models import Position, Order
from orders.serializers import PositionSerializer
from traider_bot.permissions import IsOrderOwnerOrAdmin


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


class CancelOrderView(APIView):
    permission_classes = [IsOrderOwnerOrAdmin]

    def post(self, request, order_pk):
        try:
            order = Order.objects.get(pk=order_pk)
            cancel_order(order.bot, order.order_id)
            return Response({"detail": "Order cancelled"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Get error {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
