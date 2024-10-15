from django.contrib import admin

from bots.models import Log
from main.models import Account, ActiveBot, ExchangeService, WSManager, Referral, AccountBalance


# Register your models here.


@admin.register(Account)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'is_mainnet')
    list_display_links = ('id', 'name',)
    search_fields = ('id', 'name', 'owner', 'is_mainnet')


@admin.register(ActiveBot)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'bot_id')
    list_display_links = ('id', 'bot_id',)
    search_fields = ('id', 'bot_id',)


@admin.register(ExchangeService)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_display_links = ('id', 'name',)
    search_fields = ('id', 'name',)


@admin.register(WSManager)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'status', )
    list_display_links = ('id', 'account', )
    search_fields = ('id', 'account', 'status', )


@admin.register(Referral)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'code', )
    list_display_links = ('id', 'user', 'code', )
    search_fields = ('id', 'user', 'code', )


@admin.register(AccountBalance)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'asset', 'balance', 'time_update', )
    list_display_links = ('id', 'account', 'asset', 'balance', 'time_update', )
    search_fields = ('id', 'account', 'asset', 'time_update', )
