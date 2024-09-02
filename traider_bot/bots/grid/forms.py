from django import forms

from bots.models import Grid


class GridForm(forms.ModelForm):
    class Meta:
        model = Grid

        fields = ['low_price', 'high_price', 'grid_count', ]

        widgets = {
            'low_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'high_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_count': forms.NumberInput(attrs={'class': 'form-control'}),
        }

        labels = {
            'low_price': 'Нижняя граница цены',
            'high_price': 'Верхняя граница цены',
            'grid_count': 'Кол-во сеток',
        }

    # def clean(self):
    #     cleaned_data = super().clean()
    #     average = cleaned_data.get("auto_avg")
    #     take_on_ml = cleaned_data.get("take_on_ml")
    #
    #     if not take_on_ml:
    #         cleaned_data["take_on_ml_percent"] = 0
    #     if not average:
    #         cleaned_data["bb_avg_percent"] = 0
    #         cleaned_data["dfm"] = 0
    #         cleaned_data["chw"] = 0
    #
    #     return cleaned_data
