from django.contrib import admin

from .models import Symbol, Log, StepHedge, BotModel, BBBotModel


@admin.register(BotModel)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'symbol', 'account', 'is_active', 'work_model', 'time_create', 'time_update',)
    list_display_links = ('id', 'symbol',)
    search_fields = ('symbol', 'is_active', 'work_model')


@admin.register(Symbol)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'service', 'priceScale', 'maxLeverage', 'minPrice', 'maxPrice', 'minOrderQty',)
    list_display_links = ('id', 'name',)
    search_fields = ('id', 'name', 'service__name',)


@admin.register(Log)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('bot', 'content', 'time')
    list_display_links = ('bot', 'content', 'time')
    search_fields = ('content', 'time')


@admin.register(StepHedge)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'bot', 'bot_id', 'bot_owner',)
    list_display_links = ('id', 'bot')
    search_fields = ('bot', 'bot_id', 'bot_owner',)

    @staticmethod
    def bot_id(obj):
        return obj.bot.pk

    @staticmethod
    def bot_owner(obj):
        return obj.bot.account


@admin.register(BBBotModel)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'bot', 'bot_id', 'bot_owner', 'side', 'interval', 'max_margin',)
    list_display_links = ('id', 'bot')
    search_fields = ('bot', 'bot_id', 'bot_owner',)

    @staticmethod
    def bot_id(obj):
        return obj.bot.pk

    @staticmethod
    def bot_owner(obj):
        return obj.bot.account
