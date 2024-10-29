import json
import logging
from decimal import Decimal

import requests

from collections import defaultdict
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api_2.api_aggregator import get_futures_account_balance, internal_transfer, get_user_assets
from bots.general_functions import all_symbols_update
from main.forms import InternalTransferForm
from main.models import Account, ExchangeService, Referral, AccountBalance, AccountHistory
from main.serializers import UserSerializer, AccountSerializer, ExchangeServiceSerializer, ReferralSerializer, \
    AccountBalanceSerializer, AccountTransactionHistorySerializer
from tariffs.models import UserTariff
from traider_bot.permissions import IsOwnerOrAdmin


class CurrentUserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, ]

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        self.perform_destroy(user)
        return Response({'detail': 'User deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser, ]


class AccountsViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = Account.objects.all()
        else:
            queryset = Account.objects.filter(owner=user)
        return queryset

    def list_by_owner(self, request, owner_id):
        queryset = Account.objects.filter(owner=owner_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = request.user
        user_tariff = UserTariff.objects.filter(user=user).first()

        if not user_tariff:
            return Response({"error": "Тариф не подключен"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            tariff = user_tariff.tariff
            if Account.objects.filter(owner=user).count() >= tariff.max_accounts:
                return Response(
                    {"error": f"Вы не можете создать больше {tariff.max_accounts} аккаунтов."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        instance = serializer.save()

        try:
            get_futures_account_balance(instance)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ошибка при создании аккаунта', 'error': f'{e}'}, status=200)

        url = f"http://ws-manager:8008/ws/conn/new_account/{instance.id}"
        requests.get(url)

    def perform_update(self, serializer):
        instance = serializer.save()
        url = f"http://ws-manager:8008/ws/conn/update_account/{instance.id}"
        requests.get(url)


def login_test(request):
    return render(request, 'login_test.html')


class ExchangeServiceReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExchangeService.objects.all()
    serializer_class = ExchangeServiceSerializer
    permission_classes = [IsAuthenticated]


class GetFuturesBalanceView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, acc_id):
        try:
            account = Account.objects.get(pk=acc_id)
            balance = get_futures_account_balance(account)
            return JsonResponse({'success': True, 'message': 'Balance was successfully received', 'body': balance})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class GetFuturesBalanceAllAccountsView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request):
        try:
            balances_list = defaultdict(list)
            accounts = Account.objects.filter(owner=request.user)

            for account in accounts:
                balance = get_futures_account_balance(account)
                balance['balance'] = balance.pop('fullBalance')
                balance['available_balance'] = balance.pop('availableBalance')
                balance['margin'] = round(balance['balance'] - balance['available_balance'], 2)

                balances_list[account.name].append(balance)

            return JsonResponse({'success': True, 'body': balances_list})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class GetFundBalanceView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, acc_id):
        try:
            account = Account.objects.get(pk=acc_id)
            balance = get_user_assets(account, symbol="USDT")
            return JsonResponse({'success': True, 'message': 'Balance was successfully received', 'body': balance})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class InternalTransferView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request, acc_id):
        account = get_object_or_404(Account, pk=acc_id)
        data = request.data

        form = InternalTransferForm(data)
        if form.is_valid():
            from_account_type = form.cleaned_data['fromAccountType']
            to_account_type = form.cleaned_data['toAccountType']
            symbol = form.cleaned_data['symbol']
            amount = form.cleaned_data['amount']

            internal_transfer(
                account=account,
                symbol=symbol,
                amount=amount,
                from_account_type=from_account_type,
                to_account_type=to_account_type
            )

            return Response({'success': True, 'message': 'Transfer completed successfully'})
        else:
            return Response({'success': False, 'message': 'Invalid data', 'errors': form.errors}, status=400)


class GetTrustedIPView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            trusted_ip = [
             '164.92.182.43',
            ]

            return JsonResponse({'trusted_ip': trusted_ip})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class AddReferredUserView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        referral_code = kwargs.get('referral_code')
        try:
            referral = Referral.objects.get(code=referral_code)
        except Referral.DoesNotExist:
            return Response({"detail": "Referral code does not exist."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReferralSerializer(instance=referral, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "User added to referral list."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountBalanceHistoryView(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccountBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        accounts_queryset = Account.objects.filter(owner=user)
        queryset = AccountBalance.objects.filter(account__in=accounts_queryset).order_by('-time_create')
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        grouped_data = defaultdict(list)

        for account_balance in queryset:
            account_name = account_balance.account.name
            serializer = self.get_serializer(account_balance)
            grouped_data[account_name].append(serializer.data)

        return Response(grouped_data)


class AccountTransactionHistoryView(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccountTransactionHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        accounts_queryset = Account.objects.filter(owner=user)
        queryset = AccountHistory.objects.filter(account__in=accounts_queryset)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        grouped_data = defaultdict(list)

        for transaction in queryset:
            account_name = transaction.account.name
            serializer = self.get_serializer(transaction)
            grouped_data[account_name].append(serializer.data)

        return Response(grouped_data)


class UpdateSymbolsView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            all_symbols_update()
            return Response({"detail": "Symbols updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Get error {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountWSConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            account_id = int(request.POST.get('account_id'))
            url = f"http://ws-manager:8008/ws/conn/update_account/{account_id}"
            response = requests.get(url)
            logging.info(f'{response.text}')

            return Response({"detail": f"{response.text}"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"{response.text}, {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
