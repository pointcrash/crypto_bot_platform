import traceback
from decimal import Decimal

from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api_2.api_aggregator import cancel_order, place_order, place_conditional_order, get_current_price, \
    get_position_inform
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

    def post(self, request, orderId):
        try:
            order = Order.objects.get(orderId=orderId)
            cancel_order(order.bot, order.order_id)
            return Response({"detail": "Order cancelled"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Get error {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlaceManualOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_responses = []
        order_params = []

        try:
            data = request.data

            '''
            side ("Long", "Short", "Both")
            action ("Open", "Close", "LTS", "STL")
            '''

            required_fields = ['bot_id', 'side', 'action', 'is_percent', 'percent', 'margin', 'price']

            missing_fields = [field for field in required_fields if field not in request.data]
            if missing_fields:
                return Response(
                    {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                    status=400
                )

            bot = BotModel.objects.get(pk=data.get('bot_id'))
            side = data.get('side')
            action = data.get('action')
            is_percent = data.get('is_percent')
            percent = int(data.get('percent'))
            margin = Decimal(data.get('margin'))
            price = Decimal(data.get('price'))
            amount_usdt_long = 0
            amount_usdt_short = 0
            current_price = get_current_price(bot)

            order_type = "LIMIT" if price else "MARKET"

            if is_percent is True:
                position_info = get_position_inform(bot)
                long_psn = position_info[0] if position_info[0]['side'] == 'LONG' else position_info[1]
                short_psn = position_info[0] if position_info[0]['side'] == 'SHORT' else position_info[1]

                if long_psn['qty']:
                    margin_long = Decimal(long_psn['qty']) * Decimal(long_psn['entryPrice']) / bot.leverage
                else:
                    margin_long = 0

                if short_psn['qty']:
                    margin_short = Decimal(short_psn['qty']) * Decimal(short_psn['entryPrice']) / bot.leverage
                else:
                    margin_short = 0

                amount_usdt_long = margin_long * percent / 100
                amount_usdt_short = margin_short * percent / 100

            def order_placing(action, position_side, price, current_price, bot, margin, order_type):
                if (action == 'Open' and position_side == 'LONG') or (action == 'Close' and position_side == 'SHORT'):
                    action = 'BUY'
                elif (action == 'Close' and position_side == 'LONG') or (action == 'Open' and position_side == 'SHORT'):
                    action = 'SELL'
                else:
                    raise Exception('Error from "action" validator')

                if price:
                    if action == 'BUY' and price < current_price or action == 'SELL' and price > current_price:
                        response = place_order(bot=bot, side=action, order_type=order_type, price=price,
                                               amount_usdt=margin, position_side=position_side)

                    else:
                        trigger_direction = 1 if price > current_price else 2
                        response = place_conditional_order(bot=bot, side=action, position_side=position_side,
                                                           trigger_price=price, trigger_direction=trigger_direction,
                                                           amount_usdt=margin)

                else:
                    response = place_order(bot=bot, side=action, order_type=order_type, price=current_price,
                                           amount_usdt=margin, position_side=position_side)

                order_params.append({
                    'action': action,
                    'position_side': position_side,
                    'price': price,
                    'current_price': current_price,
                    'order_type': order_type,
                    'margin': margin,
                })

                return response

            if side == "Both":
                for position_side in ['LONG', 'SHORT']:
                    if is_percent:
                        if position_side == 'LONG' and amount_usdt_long > 0:
                            margin = amount_usdt_long
                        elif position_side == 'SHORT' and amount_usdt_short > 0:
                            margin = amount_usdt_short
                        else:
                            return Response({"detail": f"Calculate order margin error. One or both positions is empty"},
                                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    order_responses.append(order_placing(action=action, position_side=position_side, price=price,
                                                         current_price=current_price, bot=bot, margin=margin,
                                                         order_type=order_type))
            else:
                position_side = side.upper()
                if is_percent:
                    if position_side == 'LONG' and amount_usdt_long > 0:
                        margin = amount_usdt_long
                    elif position_side == 'SHORT' and amount_usdt_short > 0:
                        margin = amount_usdt_short
                    else:
                        return Response({"detail": f"Calculate order margin error. One or both positions is empty"},
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                order_responses.append(order_placing(action=action, position_side=position_side, price=price,
                                                     current_price=current_price, bot=bot, margin=margin,
                                                     order_type=order_type))

            return Response({
                "detail": "The order has been sent",
                "order_responses": f"{order_responses}",
                "order_params": f"{order_params}"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "detail": f"Get error {str(e)}",
                "traceback": traceback.format_exc(),
                "order_responses": f"{order_responses}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
