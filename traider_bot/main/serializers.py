from django.contrib.auth.models import User
from rest_framework import serializers

from main.models import Account


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class AccountNameOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', ]
