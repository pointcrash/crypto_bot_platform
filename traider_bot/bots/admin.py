from django.contrib import admin

from .models import Bot, Symbol, Log, Process, Take, AvgOrder, SingleBot


@admin.register(Bot)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'symbol', 'side', 'orderType', 'qty', 'price', 'work_model',)
    list_display_links = ('id', 'symbol',)
    search_fields = ('symbol', 'orderType', 'side', 'work_model')


@admin.register(Symbol)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'priceScale', 'minLeverage', 'maxLeverage', 'minPrice', 'maxPrice', 'minOrderQty',)
    list_display_links = ('id', 'name',)
    search_fields = ('id', 'name',)


@admin.register(Log)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('bot', 'content', 'time')
    list_display_links = ('bot', 'content', 'time')
    search_fields = ('bot', 'content', 'time')


@admin.register(Process)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'pid', 'bot',)
    list_display_links = ('id', 'pid', 'bot',)


@admin.register(Take)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'bot', 'take_number', 'order_link_id', 'is_filled',)
    list_display_links = ('id', 'bot', 'order_link_id', )


@admin.register(AvgOrder)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'bot', 'order_link_id', 'is_filled',)
    list_display_links = ('id', 'bot', 'order_link_id', )


@admin.register(SingleBot)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'bot', 'single')
    list_display_links = ('id', 'bot')
