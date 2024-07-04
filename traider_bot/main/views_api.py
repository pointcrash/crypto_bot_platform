from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response

from main.models import Account
from main.serializers import UserSerializer, AccountSerializer


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class AccountsViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def list_by_owner(self, request, owner_id=None):
        accounts = Account.objects.filter(owner=owner_id)
        serializer = self.get_serializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


def login_test(request):
    return render(request, 'login_test.html')
