from rest_framework import serializers

from tariffs.models import UserTariff, Tariff


class UserTariffSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    tariff_title = serializers.ReadOnlyField(source='tariff.title')

    class Meta:
        model = UserTariff
        fields = ['id', 'tariff_title', 'tariff', 'user_username', 'user', 'created_at', ]


class TariffSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tariff
        fields = ['__all__']

