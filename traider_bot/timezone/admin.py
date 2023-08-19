from django.contrib import admin

from timezone.models import TimeZone


# Register your models here.
@admin.register(TimeZone)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'countryCode', 'countryName', 'zoneName', 'formatted_gmtoffset',)
    list_display_links = ('id', 'countryCode', 'countryName', 'zoneName',)
    search_fields = ('countryCode', 'countryName', 'zoneName', )

    def formatted_gmtoffset(self, obj):
        gmt = int(int(obj.gmtOffset) / 3600)
        if gmt > 0:
            return '+' + str(gmt)
        else:
            return gmt
