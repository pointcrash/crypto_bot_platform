from rest_framework import serializers

from purchases.models import ServiceProduct
from tariffs.models import UserTariff, Tariff


class UserTariffSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    tariff_title = serializers.ReadOnlyField(source='tariff.title')

    class Meta:
        model = UserTariff
        fields = ['id', 'tariff_title', 'tariff', 'user_username', 'user', 'created_at', ]


class TariffSerializer(serializers.ModelSerializer):
    service_product_id = serializers.SerializerMethodField()

    class Meta:
        model = Tariff
        fields = '__all__'

    def get_service_product_id(self, obj):
        return ServiceProduct.objects.filter(tariff=obj).first().id
