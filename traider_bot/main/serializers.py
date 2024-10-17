from django.contrib.auth.models import User
from django.db.models import Count
from rest_framework import serializers

from bots.models import BotModel
from main.models import Account, ExchangeService, Referral, AccountBalance, WSManager


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
    ws_status = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = '__all__'

    def get_bots_count(self, obj):
        return BotModel.objects.filter(account=obj).count()

    def get_ws_status(self, obj):
        return WSManager.objects.get(account=obj).status

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


class AccountBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountBalance
        fields = '__all__'


class ExchangeServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeService
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    account_count = serializers.SerializerMethodField()
    bots_count = serializers.SerializerMethodField()
    referral_code = serializers.SerializerMethodField()
    referral_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password']

    def get_account_count(self, obj):
        return Account.objects.filter(owner=obj).count()

    def get_bots_count(self, obj):
        return BotModel.objects.filter(owner=obj).count()

    def get_referral_code(self, obj):
        return Referral.objects.get(user=obj).code

    def get_referral_count(self, obj):
        referral = Referral.objects.filter(user=obj).annotate(referred_count=Count('referred_users')).first()
        if referral:
            return referral.referred_count
        return 0


class ReferralSerializer(serializers.ModelSerializer):
    referred_user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Referral
        fields = ['user', 'code', 'referred_user_id']

    def update(self, instance, validated_data):
        referred_user_id = validated_data.pop('referred_user_id')
        try:
            referred_user = User.objects.get(id=referred_user_id)
            instance.referred_users.add(referred_user)
            instance.save()
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist.")

        return instance
