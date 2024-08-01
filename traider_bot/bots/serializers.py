from rest_framework import serializers

from bots.models import BotModel, BBBotModel, Log, UserBotLog, StepHedge, Symbol, Grid
from main.models import Account
from main.serializers import AccountNameOnlySerializer


class StepHedgeSerializer(serializers.ModelSerializer):
    bot = serializers.PrimaryKeyRelatedField(queryset=BotModel.objects.all())

    class Meta:
        model = StepHedge
        fields = '__all__'


class BBBotModelSerializer(serializers.ModelSerializer):
    bot = serializers.PrimaryKeyRelatedField(queryset=BotModel.objects.all())

    class Meta:
        model = BBBotModel
        fields = '__all__'


class GridSerializer(serializers.ModelSerializer):
    bot = serializers.PrimaryKeyRelatedField(queryset=BotModel.objects.all())

    class Meta:
        model = Grid
        fields = '__all__'


class SymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = '__all__'


class BotModelReadOnlySerializer(serializers.ModelSerializer):
    account = AccountNameOnlySerializer(read_only=True)
    symbol = SymbolSerializer(read_only=True)
    bb = BBBotModelSerializer(read_only=True)
    zinger = StepHedgeSerializer(read_only=True)
    grid = GridSerializer(read_only=True)

    class Meta:
        model = BotModel
        fields = '__all__'


class BotModelSerializer(serializers.ModelSerializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    symbol = serializers.PrimaryKeyRelatedField(queryset=Symbol.objects.all())
    bb = serializers.PrimaryKeyRelatedField(queryset=BBBotModel.objects.all(), required=False, allow_null=True)
    zinger = serializers.PrimaryKeyRelatedField(queryset=StepHedge.objects.all(), required=False, allow_null=True)
    grid = serializers.PrimaryKeyRelatedField(queryset=Grid.objects.all(), required=False, allow_null=True)

    class Meta:
        model = BotModel
        fields = '__all__'


class BotLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = '__all__'


class UserBotLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBotLog
        fields = '__all__'
