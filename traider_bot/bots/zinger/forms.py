from django import forms
from bots.models import StepHedge


class ZingerForm(forms.ModelForm):
    class Meta:
        model = StepHedge
        fields = ['short1invest', 'long1invest', 'tp_pnl_percent_short', 'tp_pnl_percent_long', 'pnl_short_avg',
                  'pnl_long_avg', 'margin_short_avg', 'margin_long_avg', 'qty_steps', 'qty_steps_diff',
                  'is_nipple_active', 'income_percent', ]

        widgets = {
            'short1invest': forms.NumberInput(attrs={'class': 'form-control'}),
            'long1invest': forms.NumberInput(attrs={'class': 'form-control'}),
            'tp_pnl_percent_short': forms.NumberInput(attrs={'class': 'form-control', 'id': 'tp_pnl_percent'}),
            'tp_pnl_percent_long': forms.NumberInput(attrs={'class': 'form-control', 'id': 'tp_pnl_percent_long'}),
            'income_percent': forms.NumberInput(attrs={'class': 'form-control', 'id': 'tp_pnl_percent_long'}),
            'pnl_short_avg': forms.NumberInput(attrs={'class': 'form-control'}),
            'pnl_long_avg': forms.NumberInput(attrs={'class': 'form-control'}),
            'margin_short_avg': forms.NumberInput(attrs={'class': 'form-control'}),
            'margin_long_avg': forms.NumberInput(attrs={'class': 'form-control'}),
            'qty_steps': forms.NumberInput(attrs={'class': 'form-control', 'id': 'qty_steps'}),
            'qty_steps_diff': forms.NumberInput(attrs={'class': 'form-control', 'id': 'qty_steps_diff'}),
            'add_tp': forms.RadioSelect(choices=[(True, 'Add take profit'), (False, 'Replace take profit')]),
            'is_nipple_active': forms.CheckboxInput(attrs={'id': 'is_nipple_active'}),
        }
        labels = {
            'short1invest': 'SHORT - 1ST ORDER INVESTMENTS',
            'long1invest': 'LONG - 1ST ORDER INVESTMENTS',
            'tp_pnl_percent_short': '% PnL (short)',
            'tp_pnl_percent_long': '% PnL (long)',
            'income_percent': 'Желаемый процент дохода',
            'pnl_short_avg': '% PnL Short average',
            'pnl_long_avg': '% PnL Long average',
            'margin_short_avg': '% Margin Short average',
            'margin_long_avg': '% Margin Long average',
            'qty_steps': 'COUNT TICKS',
            'qty_steps_diff': 'TICKS DIFF',
            'add_tp': 'Many TP',
            'is_nipple_active': 'Nipple',
        }
