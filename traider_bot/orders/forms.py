from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = ['orderLinkId']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'side': forms.Select(attrs={'class': 'form-control'}),
            'positionIdx': forms.NumberInput(attrs={'class': 'form-control'}),
            'orderType': forms.Select(attrs={'class': 'form-control'}),
            'qty': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'timeInForce': forms.Select(attrs={'class': 'form-control'}),
        }