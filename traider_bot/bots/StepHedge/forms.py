from django import forms

from bots.models import Bot, StepHedge
from main.models import Account


class BotForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request:
            if self.request.user.is_superuser:
                self.fields['account'].queryset = Account.objects.all()
            else:
                self.fields['account'].queryset = Account.objects.filter(owner=self.request.user)

        self.fields['side'].required = False
        self.fields['orderType'].required = False
        self.fields['interval'].required = False
        self.fields['grid_avg_value'].required = False
        self.fields['chw'].required = False
        self.fields['deviation_from_lines'].required = False
        self.fields['bb_avg_percent'].required = False
        self.fields['dfm'].required = False
        self.fields['take_on_ml_percent'].required = False
        self.fields['price'].required = False

    #     self.fields['account'].label_from_instance = self.label_from_instance
    #
    # @staticmethod
    # def label_from_instance(obj):
    #     balance = get_query_account_coins_balance(obj)
    #     try:
    #         for elem in balance:
    #             if elem['coin'] == 'USDT':
    #                 return f"{obj.name} - {round(Decimal(elem['transferBalance']), 1)} USDT"
    #     except:
    #         return f"{obj.name} error"

    class Meta:
        model = Bot
        fields = ['service', 'account', 'symbol', 'side', 'interval', 'isLeverage', 'margin_type', 'orderType',
                  'qty_kline', 'd', 'auto_avg', 'bb_avg_percent',
                  'deviation_from_lines',
                  'is_percent_deviation_from_lines', 'dfm',
                  'chw', 'dfep', 'max_margin', 'take_on_ml', 'take_on_ml_percent', 'time_sleep', 'repeat',
                  'grid_avg_value', 'bin_order', 'price', ]

        widgets = {
            'qty': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.Select(attrs={'class': 'form-control'}),
            'side': forms.Select(attrs={'class': 'form-control'}),
            'orderType': forms.Select(attrs={'class': 'form-control'}),
            'margin_type': forms.Select(attrs={'class': 'form-control'}),
            'isLeverage': forms.NumberInput(attrs={'class': 'form-control', 'id': 'is_leverage'}),
            'qty_kline': forms.NumberInput(attrs={'class': 'form-control'}),
            'interval': forms.Select(attrs={'class': 'form-control'}),
            'd': forms.NumberInput(attrs={'class': 'form-control'}),
            'bb_avg_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'take_on_ml_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'deviation_from_lines': forms.NumberInput(attrs={'class': 'form-control'}),
            'dfm': forms.NumberInput(attrs={'class': 'form-control'}),
            'chw': forms.NumberInput(attrs={'class': 'form-control'}),
            'dfep': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_margin': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_sleep': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_avg_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Market'}),
        }

        labels = {
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
            'dfep': 'DFEP',
            'max_margin': 'Max Margin',
            'time_sleep': 'Request Rate (sec)',
            'repeat': 'Repeat Cycle',
            'grid_avg_value': 'Two-Sided mode: Profit/Avg Value (%)',
            'bin_order': 'Turn after ML',
            'price': 'Price',
        }


class StepHedgeForm(forms.ModelForm):
    class Meta:
        model = StepHedge
        fields = ['short1invest', 'long1invest', 'tp_pnl_percent', 'tp_pnl_percent_long', 'pnl_short_avg', 'pnl_long_avg',
                  'margin_short_avg', 'margin_long_avg', 'qty_steps', 'qty_steps_diff', 'is_nipple_active', ]

        widgets = {
            'short1invest': forms.TextInput(attrs={'class': 'form-control'}),
            'long1invest': forms.TextInput(attrs={'class': 'form-control'}),
            'tp_pnl_percent': forms.TextInput(attrs={'class': 'form-control', 'id': 'tp_pnl_percent'}),
            'tp_pnl_percent_long': forms.TextInput(attrs={'class': 'form-control', 'id': 'tp_pnl_percent_long'}),
            'pnl_short_avg': forms.TextInput(attrs={'class': 'form-control'}),
            'pnl_long_avg': forms.TextInput(attrs={'class': 'form-control'}),
            'margin_short_avg': forms.TextInput(attrs={'class': 'form-control'}),
            'margin_long_avg': forms.TextInput(attrs={'class': 'form-control'}),
            'qty_steps': forms.NumberInput(attrs={'class': 'form-control', 'id': 'qty_steps'}),
            'qty_steps_diff': forms.NumberInput(attrs={'class': 'form-control', 'id': 'qty_steps_diff'}),
            'add_tp': forms.RadioSelect(choices=[(True, 'Add take profit'), (False, 'Replace take profit')]),
            'is_nipple_active': forms.CheckboxInput(attrs={'id': 'is_nipple_active'}),
        }
        labels = {
            'short1invest': 'SHORT - 1ST ORDER INVESTMENTS',
            'long1invest': 'LONG - 1ST ORDER INVESTMENTS',
            'tp_pnl_percent': '% PnL (short)',
            'tp_pnl_percent_long': '% PnL (long)',
            'pnl_short_avg': '% PnL Short average',
            'pnl_long_avg': '% PnL Long average',
            'margin_short_avg': '% Margin Short average',
            'margin_long_avg': '% Margin Long average',
            'qty_steps': 'COUNT TICKS',
            'qty_steps_diff': 'TICKS DIFF',
            'add_tp': 'Many TP',
            'is_nipple_active': 'Nipple',
        }
