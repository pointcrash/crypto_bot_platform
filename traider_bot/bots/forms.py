from django import forms
from .models import Bot


class BotForm(forms.ModelForm):
    class Meta:
        model = Bot
        fields = '__all__'
        widgets = {
            'qty': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'side': forms.Select(attrs={'class': 'form-control'}),
            'orderType': forms.Select(attrs={'class': 'form-control'}),
            'isLeverage': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'qty': 'Quantity USDT',
            'price': 'Price',
            'category': 'Category',
            'symbol': 'Symbol',
            'side': 'Side',
            'orderType': 'Order Type',
            'isLeverage': 'Leverage',
        }