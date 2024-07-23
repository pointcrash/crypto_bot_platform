from django.contrib.auth.models import User
from rest_framework import serializers

from bots.models import BotModel
from main.models import Account, ExchangeService


def masking_data_string(string):
    length = len(string)
    if length > 2:
        start = string[:length // 4]
        end = string[-length // 4:]
        masked_string = start + '*' * (length - len(start) - len(end)) + end
    else:
        masked_string = '*' * length

    return masked_string


class AccountSerializer(serializers.ModelSerializer):
    bots_count = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = '__all__'

    def get_bots_count(self, obj):
        return BotModel.objects.filter(account=obj).count()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        api_key = representation.get('API_TOKEN', '')
        api_secret = representation.get('SECRET_KEY', '')
        if api_key:
            representation['API_TOKEN'] = masking_data_string(api_key)
        if api_secret:
            representation['SECRET_KEY'] = masking_data_string(api_secret)
        return representation


class AccountNameOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name']


class ExchangeServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeService
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    account_count = serializers.SerializerMethodField()
    bots_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password']

    def get_account_count(self, obj):
        return Account.objects.filter(owner=obj).count()

    def get_bots_count(self, obj):
        return BotModel.objects.filter(owner=obj).count()
