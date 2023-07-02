from django import forms
from .models import Bot


class BotForm(forms.ModelForm):
    class Meta:
        model = Bot
        fields = ['account', 'symbol', 'side', 'interval', 'isLeverage', 'margin_type', 'orderType', 'qty',
                  'qty_kline', 'd', 'auto_avg', 'bb_avg_percent', 'grid_avg_value', 'grid_profit_value',
                  'deviation_from_lines',
                  'is_percent_deviation_from_lines', 'dfm',
                  'chw', 'max_margin', 'take_on_ml', 'take_on_ml_percent', ]

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
            'bb_avg_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'take_on_ml_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_avg_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_profit_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'deviation_from_lines': forms.NumberInput(attrs={'class': 'form-control'}),
            'dfm': forms.NumberInput(attrs={'class': 'form-control'}),
            'chw': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_margin': forms.NumberInput(attrs={'class': 'form-control'}),
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
            'auto_avg': 'Auto Average',
            'take_on_ml': 'Middle Line',
            'take_on_ml_percent': '%',
            'bb_avg_percent': 'Average Percent',
            'grid_avg_value': 'Grid Average Value (%)',
            'grid_profit_value': 'Grid Profit Value (%)',
            'is_percent_deviation_from_lines': '%',
            'deviation_from_lines': '(± BB Deviation)',
            'dfm': 'DFM',
            'chw': 'ChW',
            'max_margin': 'Max Margin',
        }

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('orderType')
        side = cleaned_data.get('side')

        if order_type == 'Market' and side == 'Auto':
            raise forms.ValidationError("Invalid combination: orderType - 'Market' cannot have side - 'Auto'.")

        return cleaned_data
