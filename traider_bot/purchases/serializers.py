from django.contrib.auth.models import User
from rest_framework import serializers

from main.serializers import UserSerializer
from purchases.models import ServiceProduct, Purchase
from tariffs.models import UserTariff, Tariff


class ServiceProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True, required=False)

    class Meta:
        model = ServiceProduct
        fields = '__all__'


class PurchaseSerializer(serializers.ModelSerializer):
    # user_id = serializers.PrimaryKeyRelatedField(
    #     write_only=True,
    #     queryset=User.objects.all(),
    #     source='user'
    # )
    # product_id = serializers.PrimaryKeyRelatedField(
    #     write_only=True,
    #     queryset=ServiceProduct.objects.all(),
    #     source='product'
    # )
    # user = UserSerializer(read_only=True)
    product = ServiceProductSerializer(read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # ret['user'] = UserSerializer(instance.user).data if instance.user else None
        ret['product'] = ServiceProductSerializer(instance.product).data if instance.product else None
        return ret
