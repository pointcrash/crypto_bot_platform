from django import forms
from .models import TimeZone


class TimeZoneForm(forms.Form):
    time_zone = forms.ModelChoiceField(queryset=TimeZone.objects.all(), label="Сменить часовой пояс")
