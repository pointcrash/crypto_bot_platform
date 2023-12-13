from django.contrib import admin

from bots_group.models import BotsGroup


# Register your models here.
@admin.register(BotsGroup)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'time_create', 'time_update')
    list_display_links = ('id', 'name', 'owner', )
    search_fields = ('id', 'name', 'owner', 'time_create', 'time_update')