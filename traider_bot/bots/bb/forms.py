from django import forms

from bots.models import BBBotModel


class BBForm(forms.ModelForm):
    class Meta:
        model = BBBotModel

        fields = ['side', 'qty_kline', 'interval', 'd', 'take_on_ml', 'take_on_ml_percent', 'auto_avg',
                  'avg_percent', 'is_deviation_from_lines', 'percent_deviation_from_lines', 'dfm', 'chw', 'dfep',
                  'max_margin']

        widgets = {
            'side': forms.Select(attrs={'class': 'form-control'}),
            'qty_kline': forms.NumberInput(attrs={'class': 'form-control'}),
            'interval': forms.Select(attrs={'class': 'form-control'}),
            'd': forms.NumberInput(attrs={'class': 'form-control'}),
            'avg_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'take_on_ml_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'percent_deviation_from_lines': forms.NumberInput(attrs={'class': 'form-control'}),
            'dfm': forms.NumberInput(attrs={'class': 'form-control'}),
            'chw': forms.NumberInput(attrs={'class': 'form-control'}),
            'dfep': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_margin': forms.NumberInput(attrs={'class': 'form-control'}),
        }

        labels = {
            'side': 'Направление',
            'qty_kline': 'Количество свечей',
            'interval': 'Интервал свечи',
            'd': 'Отклонение',
            'auto_avg': 'Авто-усреднение',
            'take_on_ml': 'Выход на середине',
            'take_on_ml_percent': '% выхода',
            'bb_avg_percent': '% усреднения',
            'is_deviation_from_lines': 'Отклонение от линий',
            'percent_deviation_from_lines': '% отклонения',
            'dfm': '% отклонения цены',
            'chw': 'Ширина канала',
            'dfep': 'DFEP',
            'max_margin': 'Макс. маржа',
        }
