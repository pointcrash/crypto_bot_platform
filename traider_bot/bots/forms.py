from django import forms
from .models import Bot


class BotForm(forms.ModelForm):
    class Meta:
        model = Bot
        fields = ['category', 'symbol', 'side', 'interval', 'isLeverage', 'margin_type', 'orderType', 'qty',
                  'qty_kline', 'd', ]
        widgets = {
            'qty': forms.TextInput(attrs={'class': 'form-control'}),
            # 'price': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'side': forms.Select(attrs={'class': 'form-control'}),
            'orderType': forms.Select(attrs={'class': 'form-control'}),
            'margin_type': forms.Select(attrs={'class': 'form-control'}),
            'isLeverage': forms.NumberInput(attrs={'class': 'form-control'}),
            'qty_kline': forms.NumberInput(attrs={'class': 'form-control'}),
            'interval': forms.Select(attrs={'class': 'form-control'}),
            'd': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'qty': '1st order investments',
            # 'price': 'Price',
            'category': 'Category',
            'symbol': 'Symbol',
            'side': 'Side',
            'margin_type': 'Margin',
            'orderType': 'Order Type',
            'isLeverage': 'Leverage',
            'qty_kline': 'Periods',
            'interval': 'Candle Interval',
            'd': 'Deviation',
        }
