import logging
from decimal import Decimal

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from api_2.api_aggregator import place_order
from bots.general_functions import get_cur_positions_and_orders_info, custom_user_bot_logging, custom_logging

from bots.serializers import *
from bots.terminate_bot_logic import terminate_bot_with_cancel_orders, terminate_bot
from orders.models import Position, Order
from orders.serializers import PositionSerializer, OrderSerializer
from tariffs.models import UserTariff, Tariff
from traider_bot.permissions import IsOwnerOrAdmin, IsBotOwnerOrAdmin, IsAdminOrReadOnly
import traceback

logger = logging.getLogger('django')


class BBViewSet(viewsets.ModelViewSet):
    serializer_class = BBBotModelSerializer
    permission_classes = [IsAuthenticated, IsBotOwnerOrAdmin]

    def get_queryset(self):
        bot_id = self.kwargs['bot_pk']
        return BBBotModel.objects.filter(bot_id=bot_id)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        original_data = {field: getattr(instance, field) for field in request.data.keys()}
        updated_data = request.data

        changes = {
            field: {'old': original_data[field], 'new': updated_data[field]}
            for field in updated_data.keys()
            if original_data.get(field) != updated_data[field]
        }

        if changes:
            custom_user_bot_logging(instance.bot, 'Данные стратегии были изменены')
            custom_logging(instance.bot, f'Данные стратегии были изменены: {changes}')

        response = super().update(request, *args, **kwargs)

        return response


class GridViewSet(viewsets.ModelViewSet):
    serializer_class = GridSerializer
    permission_classes = [IsAuthenticated, IsBotOwnerOrAdmin]

    def get_queryset(self):
        bot_id = self.kwargs['bot_pk']
        return Grid.objects.filter(bot_id=bot_id)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        original_data = {field: getattr(instance, field) for field in request.data.keys()}
        updated_data = request.data

        changes = {
            field: {'old': original_data[field], 'new': updated_data[field]}
            for field in updated_data.keys()
            if original_data.get(field) != updated_data[field]
        }

        if changes:
            custom_user_bot_logging(instance.bot, 'Данные стратегии были изменены')
            custom_logging(instance.bot, f'Данные стратегии были изменены: {changes}')

        response = super().update(request, *args, **kwargs)

        return response


class ZingerViewSet(viewsets.ModelViewSet):
    serializer_class = StepHedgeSerializer
    permission_classes = [IsAuthenticated, IsBotOwnerOrAdmin]


class BotModelViewSet(viewsets.ModelViewSet):
    serializer_class = BotModelSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = BotModel.objects.all()
        else:
            queryset = BotModel.objects.filter(owner=user)
        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user
        user_tariff = UserTariff.objects.filter(user=user).order_by('created_at').last()

        if timezone.now() > user_tariff.expiration_time:
            tariff = Tariff.objects.get(title='Guest')
        else:
            tariff = user_tariff.tariff

        if BotModel.objects.filter(owner=user).count() >= tariff.max_bots:
            return Response(
                {"error": f"Вы не можете создать больше {tariff.max_bots} ботов."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class BotReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BotModelReadOnlySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = BotModel.objects.all()
        else:
            queryset = BotModel.objects.filter(owner=user)
        return queryset

    def list_by_account(self, request, account_id):
        queryset = BotModel.objects.filter(account=account_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def list_by_user_id(self, request, user_id):
        queryset = BotModel.objects.filter(owner=user_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BotLogsViewSet(viewsets.ModelViewSet):
    serializer_class = BotLogsSerializer
    permission_classes = [IsAdminUser, ]

    def get_queryset(self):
        bot_id = self.kwargs.get('bot_id')
        queryset = Log.objects.filter(bot=bot_id).order_by('-id')
        return queryset

    def delete_all_logs_by_bot(self, request, bot_id):
        logs = Log.objects.filter(bot=bot_id)
        if logs.exists():
            logs.delete()
            return Response({"detail": f"All logs for bot have been deleted."}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"detail": "No logs found for this bot."}, status=status.HTTP_404_NOT_FOUND)

    def delete_all_logs(self, request):
        logs = Log.objects.all()
        if logs.exists():
            logs.delete()
            return Response({"detail": f"All logs have been deleted."}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"detail": "No logs found for this bot."}, status=status.HTTP_404_NOT_FOUND)


class UserBotLogViewSet(viewsets.ModelViewSet):
    serializer_class = UserBotLogSerializer

    def get_queryset(self):
        bot_id = self.kwargs.get('bot_id')
        queryset = UserBotLog.objects.filter(bot=bot_id).order_by('-id')
        return queryset

    def delete_all_logs_by_bot(self, request, bot_id):
        logs = UserBotLog.objects.filter(bot=bot_id)
        if logs.exists():
            logs.delete()
            return Response({"detail": f"All user-logs for bot have been deleted."}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"detail": "No user-logs found for this bot."}, status=status.HTTP_404_NOT_FOUND)


class SymbolViewSet(viewsets.ModelViewSet):
    queryset = Symbol.objects.all()
    serializer_class = SymbolSerializer
    permission_classes = [IsAdminOrReadOnly]


class StopBotView(APIView):
    permission_classes = [IsAuthenticated, IsBotOwnerOrAdmin]

    def post(self, request, bot_id, event_number):
        try:
            bot = get_object_or_404(BotModel, pk=bot_id)
            user = request.user
            logger.info(
                f'{user} остановил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}. Event number-{event_number}')

            # bot.is_active = False
            # bot.save(update_fields=['is_active'])

            if event_number == 1:
                terminate_bot(bot, user)
            elif event_number == 2:
                terminate_bot_with_cancel_orders(bot, user)

            return JsonResponse({'success': True, 'message': 'Bot stopped successfully'})
        except Exception as e:
            logger.error(f'Error stopping bot: {e}')
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class DeleteBotView(APIView):
    permission_classes = [IsAuthenticated, IsBotOwnerOrAdmin]

    def post(self, request, bot_id, event_number):
        try:
            bot = get_object_or_404(BotModel, pk=bot_id)
            user = request.user
            logger.info(
                f'{user} удалил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}. Event number-{event_number}')

            if event_number == 1:
                terminate_bot(bot, user)
            elif event_number == 2:
                terminate_bot_with_cancel_orders(bot, user)

            bot.delete()
            return JsonResponse({'success': True, 'message': 'Bot deleted successfully'})

        except Exception as e:
            logger.error(f'Error deleting bot: {e}')
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class BotStartView(APIView):
    permission_classes = [IsAuthenticated, IsBotOwnerOrAdmin]

    def post(self, request, bot_id):
        try:
            bot = get_object_or_404(BotModel, pk=bot_id)
            user = request.user
            logger.info(
                f'{user} запустил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}')

            bot.is_active = True
            bot.bot_time_start = timezone.now()
            bot.save(update_fields=['is_active', 'bot_time_start'])

            return JsonResponse({'success': True, 'message': 'Bot started successfully'})

        except Exception as e:
            logger.error(f'Error starting bot: {e}')
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class DeactivateAllMyBotsView(APIView):
    permission_classes = [IsAuthenticated, IsBotOwnerOrAdmin]

    def post(self, request):
        try:
            user = request.user
            bots = BotModel.objects.filter(owner=user, is_active=True)
            bots.update(is_active=False)

            for bot in bots:
                cache.set(f'close_ws_{bot.id}', True, timeout=60)

            return JsonResponse({'success': True, 'message': 'All bots stopped successfully'})

        except Exception as e:
            logger.error(f'Error stopping all bots: {e}')
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class CloseSelectedPositionView(APIView):
    permission_classes = [IsAuthenticated, IsBotOwnerOrAdmin]

    def post(self, request, bot_id):
        try:
            qty = request.query_params.get('qty')
            psn_side = request.query_params.get('side')

            bot = BotModel.objects.get(pk=bot_id)
            side = 'SELL' if psn_side == 'LONG' else 'BUY'
            qty = abs(Decimal(qty))
            response = place_order(bot=bot, side=side, position_side=psn_side, qty=qty, price=None, order_type='MARKET')

            return JsonResponse({'success': True, 'message': 'Position closed', 'response': response}, status=200)
        except Exception as e:
            logger.error(f'Error stopping all bots: {e}')
            return JsonResponse({'success': False, 'message': str(e), '**traceback**': str(traceback.format_exc())},
                                status=500)


class GetOrdersAndPositionsHistoryBotsView(APIView):
    permission_classes = [IsAuthenticated, IsBotOwnerOrAdmin]

    def get(self, request, bot_id):
        try:
            bot = get_object_or_404(BotModel, pk=bot_id)

            order_history = Order.objects.filter(account=bot.account, symbol_name=bot.symbol.name,
                                                 status='FILLED').order_by('-time_update')[:100]
            position_history = Position.objects.filter(account=bot.account, symbol_name=bot.symbol.name).order_by(
                '-time_update')

            psn_his_long = list(position_history.filter(side='LONG'))
            psn_his_short = list(position_history.filter(side='SHORT'))
            filtered_positions = []

            if psn_his_long:
                filtered_positions.append(psn_his_long[0])

                for current, next_pos in zip(psn_his_long[:-1], psn_his_long[1:]):
                    if current.qty != next_pos.qty:
                        filtered_positions.append(next_pos)

            if psn_his_short:
                filtered_positions.append(psn_his_short[0])

                for current, next_pos in zip(psn_his_short[:-1], psn_his_short[1:]):
                    if current.qty != next_pos.qty:
                        filtered_positions.append(next_pos)

            filtered_positions.sort(key=lambda x: x.id, reverse=True)
            filtered_positions = filtered_positions[:100]

            filtered_positions_data = PositionSerializer(filtered_positions, many=True).data
            order_history_serialized = OrderSerializer(order_history, many=True).data

            positions, orders = get_cur_positions_and_orders_info(bot)

            return JsonResponse(
                {
                    'success': True,
                    'data': {
                        'position_history': filtered_positions_data,
                        'order_history': order_history_serialized,
                        'positions': positions,
                        'orders': orders
                    }
                }
            )

        except Exception as e:
            logger.error(f'Error stopping all bots: {e}')
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
