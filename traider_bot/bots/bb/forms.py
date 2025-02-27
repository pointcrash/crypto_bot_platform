from django import forms

from bots.models import BBBotModel


class BBForm(forms.ModelForm):
    class Meta:
        model = BBBotModel

        fields = ['side', 'qty_kline', 'interval', 'd', 'take_on_ml', 'take_after_ml', 'take_on_ml_percent', 'auto_avg',
                  'avg_percent', 'is_deviation_from_lines', 'percent_deviation_from_lines', 'dfm', 'chw', 'dfep',
                  'max_margin', 'hard_avg', 'hard_avg_type', 'hard_avg_percent', 'endless_cycle',
                  'stop_loss', 'stop_bot_after_loss', 'stop_loss_value', 'stop_loss_value_choice',
                  'trailing_in', 'trailing_in_percent', 'trailing_out', 'trailing_out_percent', ]

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

            'hard_avg_type': forms.Select(attrs={'class': 'form-control'}),
            'hard_avg_percent': forms.NumberInput(attrs={'class': 'form-control'}),

            'stop_loss_value_choice': forms.Select(attrs={'class': 'form-control'}),
            'stop_loss_value': forms.NumberInput(attrs={'class': 'form-control'}),

            'trailing_in_percent': forms.Select(attrs={'class': 'form-control'}),
            'trailing_out_percent': forms.Select(attrs={'class': 'form-control'}),
        }

        labels = {
            'side': 'Направление',
            'qty_kline': 'Количество свечей',
            'interval': 'Интервал свечи',
            'd': 'Отклонение',
            'auto_avg': 'Усреднение по Боллинджеру',
            'take_on_ml': 'Выход на середине',
            'take_after_ml': 'Докуп после ML',
            'take_on_ml_percent': '% выхода',
            'bb_avg_percent': '% усреднения',
            'is_deviation_from_lines': 'Вход за линией',
            'percent_deviation_from_lines': '% отклонения',
            'dfm': '% отклонения',
            'chw': 'Ширина канала',
            'dfep': 'DFEP',
            'max_margin': 'Макс. маржа',

            'hard_avg': 'Простое усреднение',
            'hard_avg_type': 'Условие',
            'hard_avg_percent': 'Процент',
            'endless_cycle': 'Кол-во циклов: 1/∞',

            'stop_loss': 'StopLoss',
            'stop_bot_after_loss': 'Остановка бота',
            'stop_loss_value': 'Значение',
            'stop_loss_value_choice': 'Условие',

            'trailing_in': 'Трейлинг входа',
            'trailing_in_percent': 'Трейлинг процент',
            'trailing_out': 'Трейлинг выхода',
            'trailing_out_percent': 'Трейлинг процент',

        }

    def clean(self):
        cleaned_data = super().clean()
        average = cleaned_data.get("auto_avg")
        take_on_ml = cleaned_data.get("take_on_ml")

        if not take_on_ml:
            cleaned_data["take_on_ml_percent"] = 0
        if not average:
            cleaned_data["bb_avg_percent"] = 0
            cleaned_data["dfm"] = 0
            cleaned_data["chw"] = 0

        return cleaned_data
