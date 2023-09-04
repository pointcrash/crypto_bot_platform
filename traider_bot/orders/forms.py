from decimal import Decimal
from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        SIDE_CHOICES = (
            ('Buy', 'Buy'),
            ('Sell', 'Sell'),
        )

        model = Order
        fields = ['side', 'qty', 'isLeverage', 'char_price', 'is_take', 'takeProfit', 'stopLoss']

        widgets = {
            'qty': forms.TextInput(attrs={'class': 'form-control'}),
            'side': forms.Select(choices=SIDE_CHOICES, attrs={'class': 'form-control'}),
            'isLeverage': forms.NumberInput(attrs={'class': 'form-control'}),
            'char_price': forms.TextInput(attrs={'class': 'form-control'}),
            'takeProfit': forms.TextInput(attrs={'class': 'form-control'}),
            'stopLoss': forms.TextInput(attrs={'class': 'form-control'}),
        }

        labels = {
            'qty': 'Quantity',
            'char_price': 'Price',
            'is_take': 'Open/Close',
            'isLeverage': 'Leverage',
        }
