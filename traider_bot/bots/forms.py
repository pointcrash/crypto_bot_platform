from decimal import Decimal
from django import forms

from api_v5 import get_query_account_coins_balance
from main.models import Account
from .models import Bot


class BotForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(owner=user)
        self.fields['account'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        balance = get_query_account_coins_balance(obj)
        try:
            for elem in balance:
                if elem['coin'] == 'USDT':
                    return f"{obj.name} - {round(Decimal(elem['transferBalance']), 1)} USDT"
        except:
            return f"{obj.name} error"

    class Meta:
        model = Bot
        fields = ['account', 'symbol', 'side', 'interval', 'isLeverage', 'margin_type', 'orderType', 'qty',
                  'qty_kline', 'd', 'auto_avg', 'bb_avg_percent',
                  'deviation_from_lines',
                  'is_percent_deviation_from_lines', 'dfm',
                  'chw', 'max_margin', 'take_on_ml', 'take_on_ml_percent', 'time_sleep', 'repeat', ]

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
            'deviation_from_lines': forms.NumberInput(attrs={'class': 'form-control'}),
            'dfm': forms.NumberInput(attrs={'class': 'form-control'}),
            'chw': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_margin': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_sleep': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'qty': '1st order investments $',
            'account': 'Account',
            'symbol': 'Symbol',
            'side': 'Side',
            'margin_type': 'Margin',
            'orderType': 'Order Type',
            'isLeverage': 'Leverage',
            'interval': 'Candle Interval',
            'qty_kline': 'Periods',
            'd': 'Deviation',
            'auto_avg': 'Auto Average',
            'take_on_ml': 'Middle Line',
            'take_on_ml_percent': '%',
            'bb_avg_percent': 'Average Percent',
            'is_percent_deviation_from_lines': '%',
            'deviation_from_lines': '(± BB Deviation)',
            'dfm': 'DFM',
            'chw': 'ChW',
            'max_margin': 'Max Margin',
            'time_sleep': 'Request Rate (sec)',
            'repeat': 'Repeat Cycle',
        }

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('orderType')
        side = cleaned_data.get('side')
        deviation_from_lines = cleaned_data.get('deviation_from_lines')
        is_percent_deviation_from_lines = cleaned_data.get('is_percent_deviation_from_lines')
        symbol = cleaned_data.get('symbol')
        qty = cleaned_data.get('qty')

        if qty is None:
            raise forms.ValidationError("Invalid '1st order investments' value. Only whole numbers")

        if order_type == 'Market' and side == 'Auto':
            raise forms.ValidationError("Invalid combination: orderType - 'Market' cannot have side - 'Auto'.")

        if deviation_from_lines:
            if not is_percent_deviation_from_lines and deviation_from_lines < Decimal(symbol.minPrice):
                raise forms.ValidationError(f"Minimum '± BB Deviation' value = {symbol.minPrice}")

        if qty < Decimal(symbol.minPrice) or qty > Decimal(symbol.maxPrice):
            raise forms.ValidationError(
                f"Invalid '1st order investments' value: \nmin value = {symbol.minPrice},\n max value = {symbol.maxPrice}")

        return cleaned_data


class GridBotForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(owner=user)
        self.fields['account'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        balance = get_query_account_coins_balance(obj)
        try:
            for elem in balance:
                if elem['coin'] == 'USDT':
                    return f"{obj.name} - {round(Decimal(elem['transferBalance']), 1)} USDT"
        except:
            return f"{obj.name} error"

    class Meta:
        model = Bot
        fields = ['account', 'symbol', 'side', 'interval', 'isLeverage', 'margin_type', 'orderType', 'qty',
                  'auto_avg', 'grid_avg_value', 'grid_profit_value', 'bb_avg_percent',
                  'deviation_from_lines', 'is_percent_deviation_from_lines', 'max_margin', 'qty_kline', 'd',
                  'time_sleep', 'repeat', 'grid_take_count', ]

        widgets = {
            'qty': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            # 'category': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.Select(attrs={'class': 'form-control'}),
            'side': forms.Select(attrs={'class': 'form-control'}),
            'orderType': forms.Select(attrs={'class': 'form-control'}),
            'margin_type': forms.Select(attrs={'class': 'form-control'}),
            'isLeverage': forms.NumberInput(attrs={'class': 'form-control'}),
            'interval': forms.Select(attrs={'class': 'form-control'}),
            'qty_kline': forms.NumberInput(attrs={'class': 'form-control'}),
            'd': forms.NumberInput(attrs={'class': 'form-control'}),
            'bb_avg_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_avg_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_profit_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_take_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'deviation_from_lines': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_margin': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_sleep': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'qty': '1st order investments $',
            'account': 'Account',
            # 'category': 'Category',
            'symbol': 'Symbol',
            'side': 'Side',
            'margin_type': 'Margin',
            'orderType': 'Order Type',
            'isLeverage': 'Leverage',
            'interval': 'Candle Interval',
            'auto_avg': 'Auto Average',
            'grid_avg_value': 'Grid Average Value (%)',
            'grid_profit_value': 'Grid Profit Value (%)',
            'grid_take_count': 'Takes Count',
            'bb_avg_percent': 'Average Percent',
            'deviation_from_lines': '± BB Deviation',
            'is_percent_deviation_from_lines': '%',
            'qty_kline': 'Periods',
            'd': 'Deviation',
            'max_margin': 'Max Margin',
            'time_sleep': 'Request Rate (sec)',
            'repeat': 'Repeat Cycle',
        }

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('orderType')
        side = cleaned_data.get('side')
        deviation_from_lines = cleaned_data.get('deviation_from_lines')
        is_percent_deviation_from_lines = cleaned_data.get('is_percent_deviation_from_lines')
        symbol = cleaned_data.get('symbol')
        qty = cleaned_data.get('qty')
        orderType = cleaned_data.get('orderType')
        auto_avg = cleaned_data.get('auto_avg')
        margin = cleaned_data.get('max_margin')

        if not margin and auto_avg:
            raise forms.ValidationError("Invalid 'Max Margin' value")

        if qty is None:
            raise forms.ValidationError("Invalid '1st order investments' value. Only whole numbers")

        if order_type == 'Market' and side == 'Auto':
            raise forms.ValidationError("Invalid combination: orderType - 'Market' cannot have side - 'Auto'.")

        if deviation_from_lines:
            if not is_percent_deviation_from_lines and deviation_from_lines < Decimal(symbol.minPrice):
                raise forms.ValidationError(f"Minimum '± BB Deviation' value = {symbol.minPrice}")

        elif not deviation_from_lines and orderType == "Limit":
            raise forms.ValidationError("If 'Order Type' - Limit, '± BB Deviation' must be filled")

        if qty < Decimal(symbol.minPrice) or qty > Decimal(symbol.maxPrice):
            raise forms.ValidationError(
                f"Invalid '1st order investments' value: min value = {symbol.minPrice}, max value = {symbol.maxPrice}")

        return cleaned_data


class HedgeGridBotForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request:
            self.fields['account'].queryset = Account.objects.filter(owner=self.request.user)
        self.fields['account'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        balance = get_query_account_coins_balance(obj)
        try:
            for elem in balance:
                if elem['coin'] == 'USDT':
                    return f"{obj.name} - {round(Decimal(elem['transferBalance']), 1)} USDT"
        except:
            return f"{obj.name} error"

    class Meta:
        model = Bot
        fields = ['account', 'symbol', 'isLeverage', 'qty', 'grid_avg_value', 'grid_profit_value', 'max_margin',
                  'time_sleep', 'bb_avg_percent', ]

        widgets = {
            'qty': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.Select(attrs={'class': 'form-control'}),
            'isLeverage': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_avg_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'bb_avg_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_profit_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_margin': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_sleep': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'qty': '1st order investments $',
            'account': 'Account',
            'symbol': 'Symbol',
            'isLeverage': 'Leverage',
            'grid_avg_value': 'Grid Average Value (%)',
            'grid_profit_value': 'Grid Profit Value (%)',
            'max_margin': 'Max Margin',
            'time_sleep': 'Request Rate (sec)',
            'bb_avg_percent': 'Average Percent',
        }
