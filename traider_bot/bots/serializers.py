from rest_framework import serializers

from bots.models import BotModel, BBBotModel, Log, UserBotLog, StepHedge
from main.serializers import AccountNameOnlySerializer


class StepHedgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepHedge
        fields = '__all__'


class BBBotModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = BBBotModel
        fields = '__all__'


class BotModelSerializer(serializers.ModelSerializer):
    account = AccountNameOnlySerializer()
    bb = BBBotModelSerializer()
    zinger = StepHedgeSerializer()

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
