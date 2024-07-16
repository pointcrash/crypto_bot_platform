import logging
import threading
import time

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from bots.bb.logic.start_logic import bb_worker
from bots.grid.logic.start_logic import grid_worker
from bots.terminate_bot_logic import terminate_bot, terminate_bot_with_cancel_orders, \
    terminate_bot_with_cancel_orders_and_drop_positions
from bots.zinger.logic_market.start_logic import zinger_worker_market

from bots.serializers import *
from traider_bot.permissions import IsOwnerOrAdmin, IsBotOwnerOrAdmin, IsAdminOrReadOnly

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


class BotLogsViewSet(viewsets.ModelViewSet):
    serializer_class = BotLogsSerializer
    permission_classes = [IsAdminUser, ]

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


class SymbolViewSet(viewsets.ModelViewSet):
    queryset = Symbol.objects.all()
    serializer_class = SymbolSerializer
    permission_classes = [IsAdminOrReadOnly]


class StopBotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, bot_id, event_number):
        try:
            bot = get_object_or_404(BotModel, pk=bot_id)
            user = request.user
            logger.info(
                f'{user} остановил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}. Event number-{event_number}')

            if event_number == 1:
                terminate_bot(bot, user)
            elif event_number == 2:
                terminate_bot_with_cancel_orders(bot, user)
            elif event_number == 3:
                terminate_bot_with_cancel_orders_and_drop_positions(bot, user)
            else:
                return JsonResponse({'success': False, 'message': 'Invalid event number'}, status=400)
            return JsonResponse({'success': True, 'message': 'Bot stopped successfully'})
        except Exception as e:
            logger.error(f'Error stopping bot: {e}')
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class DeleteBotView(APIView):
    permission_classes = [IsAuthenticated]

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
            elif event_number == 3:
                terminate_bot_with_cancel_orders_and_drop_positions(bot, user)
            else:
                return JsonResponse({'success': False, 'message': 'Invalid event number'}, status=400)

            bot.delete()
            return JsonResponse({'success': True, 'message': 'Bot deleted successfully'})

        except Exception as e:
            logger.error(f'Error deleting bot: {e}')
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class BotStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, bot_id):
        try:
            bot = get_object_or_404(BotModel, pk=bot_id)
            bot_thread = None
            user = request.user
            logger.info(
                f'{user} запустил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}')

            bot.is_active = True
            bot.save()

            if bot.work_model == 'bb':
                pass
                # bot_thread = threading.Thread(target=bb_worker, args=(bot,), name=f'BotThread_{bot.id}')

            if bot.work_model == 'grid':
                pass
                # bot_thread = threading.Thread(target=grid_worker, args=(bot,), name=f'BotThread_{bot.id}')

            elif bot.work_model == 'zinger':
                pass
                # bot_thread = threading.Thread(target=zinger_worker_market, args=(bot,), name=f'BotThread_{bot.id}')

            if bot_thread is not None:
                pass
                # bot_thread.start()

            return JsonResponse({'success': True, 'message': 'Bot started successfully'})

        except Exception as e:
            logger.error(f'Error starting bot: {e}')
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class DeactivateAllMyBotsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            BotModel.objects.filter(owner=user, is_active=True).update(is_active=False)
            time.sleep(3)

            return JsonResponse({'success': True, 'message': 'All bots stopped successfully'})

        except Exception as e:
            logger.error(f'Error stopping all bots: {e}')
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

# def stop_bot(request, bot_id, event_number):
#     try:
#         bot = get_object_or_404(BotModel, pk=bot_id)
#         user = request.user
#         logger.info(
#             f'{user} остановил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}. Event number-{event_number}')
#
#         if event_number == 1:
#             terminate_bot(bot, user)
#         elif event_number == 2:
#             terminate_bot_with_cancel_orders(bot, user)
#         elif event_number == 3:
#             terminate_bot_with_cancel_orders_and_drop_positions(bot, user)
#         else:
#             return JsonResponse({'success': False, 'message': 'Invalid event number'}, status=400)
#         return JsonResponse({'success': True, 'message': 'Bot stopped successfully'})
#     except Exception as e:
#         logger.error(f'Error stopping bot: {e}')
#         return JsonResponse({'success': False, 'message': str(e)}, status=500)
#
#
# def delete_bot(request, bot_id, event_number):
#     try:
#         bot = get_object_or_404(BotModel, pk=bot_id)
#         user = request.user
#         logger.info(
#             f'{user} удалил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}. Event number-{event_number}')
#
#         if event_number == 1:
#             terminate_bot(bot, user)
#         elif event_number == 2:
#             terminate_bot_with_cancel_orders(bot, user)
#         elif event_number == 3:
#             terminate_bot_with_cancel_orders_and_drop_positions(bot, user)
#         else:
#             return JsonResponse({'success': False, 'message': 'Invalid event number'}, status=400)
#
#         bot.delete()
#         return JsonResponse({'success': True, 'message': 'Bot deleted successfully'})
#
#     except Exception as e:
#         logger.error(f'Error deleting bot: {e}')
#         return JsonResponse({'success': False, 'message': str(e)}, status=500)
#
#
# def bot_start(request, bot_id):
#     try:
#         bot = get_object_or_404(BotModel, pk=bot_id)
#         bot_thread = None
#         user = request.user
#         logger.info(
#             f'{user} запустил бота ID: {bot.id}, Account: {bot.account}, Coin: {bot.symbol.name}')
#
#         bot.is_active = True
#         bot.save()
#
#         if bot.work_model == 'bb':
#             pass
#             # bot_thread = threading.Thread(target=bb_worker, args=(bot,), name=f'BotThread_{bot.id}')
#
#         if bot.work_model == 'grid':
#             pass
# #             bot_thread = threading.Thread(target=grid_worker, args=(bot,), name=f'BotThread_{bot.id}')
#
#         elif bot.work_model == 'zinger':
#             pass
# #             bot_thread = threading.Thread(target=zinger_worker_market, args=(bot,), name=f'BotThread_{bot.id}')
#
#         if bot_thread is not None:
#             pass
#             # bot_thread.start()
#
#         return JsonResponse({'success': True, 'message': 'Bot started successfully'})
#
#
#     except Exception as e:
#         logger.error(f'Error deleting bot: {e}')
#         return JsonResponse({'success': False, 'message': str(e)}, status=500)
#
#
# def deactivate_all_my_bots(request):
#     try:
#         user = request.user
#         BotModel.objects.filter(owner=user, is_active=True).update(is_active=False)
#         time.sleep(3)
#
#         return JsonResponse({'success': True, 'message': 'All bots stopped successfully'})
#
#     except Exception as e:
#         logger.error(f'Error deleting bot: {e}')
#         return JsonResponse({'success': False, 'message': str(e)}, status=500)
