from rest_framework import serializers

from purchases.models import ServiceProduct
from tariffs.models import UserTariff, Tariff


class TariffSerializer(serializers.ModelSerializer):
    service_product_id = serializers.SerializerMethodField()

    class Meta:
        model = Tariff
        fields = '__all__'

    def get_service_product_id(self, obj):
        product = ServiceProduct.objects.filter(tariff=obj).first()
        return product.id if product else ''


class UserTariffSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    # tariff_title = serializers.ReadOnlyField(source='tariff.title')
    tariff_data = TariffSerializer(source='tariff', read_only=True)

    class Meta:
        model = UserTariff
        fields = ['id', 'user_username', 'user', 'created_at', 'expiration_time', 'tariff_data', ]
