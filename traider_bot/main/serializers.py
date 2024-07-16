from django.contrib.auth.models import User
from rest_framework import serializers

from bots.models import BotModel
from main.models import Account


class AccountSerializer(serializers.ModelSerializer):
    bots_count = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = '__all__'

    def get_bots_count(self, obj):
        return BotModel.objects.filter(account=obj).count()


class AccountNameOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    account_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password']

    def get_account_count(self, obj):
        return Account.objects.filter(owner=obj).count()
