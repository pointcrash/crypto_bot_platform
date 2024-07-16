from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from main.models import Account
from main.serializers import UserSerializer, AccountSerializer
from traider_bot.permissions import IsOwnerOrAdmin


class CurrentUserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, ]

    def get_object(self):
        return self.request.user


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


def login_test(request):
    return render(request, 'login_test.html')
