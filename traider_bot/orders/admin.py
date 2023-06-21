from django.contrib import admin

from .forms import OrderForm
from .models import Order


@admin.register(Order)
class OrdersAdmin(admin.ModelAdmin):
    form = OrderForm
    list_display = ('id', 'symbol', 'side', 'orderType', 'qty', 'price', )
    list_display_links = ('id', 'symbol', )
    search_fields = ('symbol', 'orderType', 'side')
