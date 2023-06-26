from django.contrib import admin

from main.models import Log


# Register your models here.
@admin.register(Log)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'content', )

