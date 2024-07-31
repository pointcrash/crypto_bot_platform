from django.contrib import admin

from tariffs.models import Tariff, UserTariff


# Register your models here.

@admin.register(Tariff)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'max_accounts', 'max_bots', 'max_income_per_month', 'response_time_from_support')
    list_display_links = ('id', 'title')
    search_fields = ('id', 'title')


@admin.register(UserTariff)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'tariff', 'created_at')
    list_display_links = ('id', 'user', 'tariff',)
    search_fields = ('id', 'user', 'tariff')
