from django import forms
from bots.models import StepHedge


class ZingerForm(forms.ModelForm):
    class Meta:
        model = StepHedge
        fields = ['short1invest', 'long1invest', 'tp_pnl_percent_short', 'tp_pnl_percent_long', 'pnl_short_avg',
                  'pnl_long_avg', 'margin_short_avg', 'margin_long_avg', 'qty_steps', 'qty_steps_diff',
                  'is_nipple_active', 'income_percent', 'tp_trailing', 'tp_trailing_percent',
                  'reinvest_long', 'reinvest_short', 'reinvest_with_leverage', 'reinvest_count_ticks', ]

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
            'tp_trailing': forms.CheckboxInput(attrs={'id': 'tp_trailing'}),
            'tp_trailing_percent': forms.Select(attrs={'class': 'form-control'}),
            'reinvest_long': forms.CheckboxInput(attrs={'id': 'reinvest_long'}),
            'reinvest_short': forms.CheckboxInput(attrs={'id': 'reinvest_short'}),
            'reinvest_with_leverage': forms.CheckboxInput(attrs={'id': 'reinvest_with_leverage'}),
            'reinvest_count_ticks': forms.NumberInput(attrs={'class': 'form-control'}),
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
            'qty_steps': 'Кол-во тиков',
            'qty_steps_diff': 'TICKS DIFF',
            'add_tp': 'Many TP',
            'is_nipple_active': 'Ниппель',
            'tp_trailing': 'Трейлинг закрытия',
            'tp_trailing_percent': '% отката цены',
            'reinvest_long': 'Лонг',
            'reinvest_short': 'Шорт',
            'reinvest_with_leverage': 'Реинвест с учетом плеча',
            'reinvest_count_ticks': 'С какого выхода начать',
        }


class AverageZingerForm(forms.Form):
    qty = forms.DecimalField(max_digits=11, decimal_places=1, widget=forms.NumberInput(attrs={'class': 'form-control'}),
                             label='Кол-во')

    NOMINAL_CHOICES = [
        ('%', '%'),
        ('$', '$'),
    ]
    nominal = forms.ChoiceField(choices=NOMINAL_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}),
                                label='% / $')

    price = forms.DecimalField(max_digits=20, decimal_places=10, required=False,
                               widget=forms.NumberInput(attrs={'class': 'form-control'}), label='Цена')

    ORDER_CHOICES = [
        ('MARKET', 'Market'),
        ('LIMIT', 'Limit'),
    ]
    type = forms.ChoiceField(choices=ORDER_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}),
                             label='Тип ордера')
    PSN_CHOICES = [
        ('BOTH', 'Both'),
        ('LONG', 'Long'),
        ('SHORT', 'Short'),
    ]
    psnSide = forms.ChoiceField(choices=PSN_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}),
                                label='Позиция')

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get("type")
        price = cleaned_data.get("price")

        if order_type == 'LIMIT' and not price:
            raise forms.ValidationError("Укажите цену для лимитного ордера")

        return cleaned_data
