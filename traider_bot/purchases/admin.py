from django.contrib import admin

from purchases.models import ServiceProduct, Purchase


# Register your models here.

@admin.register(ServiceProduct)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'type', 'price', 'created_at')
    list_display_links = ('id', 'title',)
    search_fields = ('id', 'title',)

@admin.register(Purchase)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'order_id', 'created_at', 'enrolled', 'completed')
    list_display_links = ('id', 'product', 'order_id', 'created_at', 'enrolled', 'completed',)
    search_fields = ('id', 'product', 'order_id', 'created_at', 'enrolled', 'completed',)
