from django import forms
from .models import Bot


class BotForm(forms.ModelForm):
    class Meta:
        model = Bot
        fields = ['account', 'symbol', 'side', 'interval', 'isLeverage', 'margin_type', 'orderType', 'qty',
                  'qty_kline', 'd', ]

        widgets = {
            'qty': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.Select(attrs={'class': 'form-control'}),
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
            'account': 'Account',
            'symbol': 'Symbol',
            'side': 'Side',
            'margin_type': 'Margin',
            'orderType': 'Order Type',
            'isLeverage': 'Leverage',
            'qty_kline': 'Periods',
            'interval': 'Candle Interval',
            'd': 'Deviation',
        }

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('orderType')
        side = cleaned_data.get('side')

        if order_type == 'Market' and side == 'Auto':
            raise forms.ValidationError("Invalid combination: orderType - 'Market' cannot have side - 'Auto'.")

        return cleaned_data
