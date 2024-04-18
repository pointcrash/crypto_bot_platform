from decimal import Decimal
from django import forms


class OrderCreateForm(forms.ModelForm):
    pass
    # class Meta:
    #     SIDE_CHOICES = (
    #         ('Buy', 'Buy'),
    #         ('Sell', 'Sell'),
    #     )
    #     ORDER_TYPE_CHOICES = (
    #         ('Market', 'Market'),
    #         ('Limit', 'Limit'),
    #     )
    #
    #     model = Order
    #     fields = ['side', 'orderType', 'qty', 'isLeverage', 'char_price', 'is_take', 'takeProfit', 'stopLoss', ]
    #
    # widgets = {
    #     'qty': forms.TextInput(attrs={'class': 'form-control'}),
    #     'side': forms.Select(choices=SIDE_CHOICES, attrs={'class': 'form-control'}),
    #     'orderType': forms.Select(choices=ORDER_TYPE_CHOICES, attrs={'class': 'form-control'}),
    #     'isLeverage': forms.NumberInput(attrs={'class': 'form-control'}),
    #     'char_price': forms.TextInput(attrs={'class': 'form-control'}),
    #     'takeProfit': forms.TextInput(attrs={'class': 'form-control'}),
    #     'stopLoss': forms.TextInput(attrs={'class': 'form-control'}),
    # }
    #
    #     labels = {
    #         'qty': 'Quantity',
    #         'char_price': 'Price',
    #         'is_take': 'Close',
    #         'isLeverage': 'Leverage',
    #     }


class OrderCustomForm(forms.Form):
    qty = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.NumberInput(attrs={'class': 'form-control'}),
                             label='Количество монет')
    price = forms.DecimalField(max_digits=20, decimal_places=10, required=False,
                               widget=forms.NumberInput(attrs={'class': 'form-control'}), label='Цена')
    triggerPrice = forms.DecimalField(max_digits=20, decimal_places=10, required=False,
                                      widget=forms.NumberInput(attrs={'class': 'form-control'}), label='Триггер цена')
    ORDER_CHOICES = [
        ('MARKET', 'Market'),
        ('LIMIT', 'Limit'),
    ]
    type = forms.ChoiceField(choices=ORDER_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}),
                             label='Тип ордера')
    SIDE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    side = forms.ChoiceField(choices=SIDE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}),
                             label='Купить/Продать')
    PSN_CHOICES = [
        ('LONG', 'Long'),
        ('SHORT', 'Short'),
    ]
    psnSide = forms.ChoiceField(choices=PSN_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}),
                                label='Позиция')

    # class Meta:
    #     fields = ['qty', 'price', 'triggerPrice', 'type', 'side', 'psnSide']

    # widgets = {
    #     'qty': forms.NumberInput(attrs={'class': 'form-control'}),
    #     'price': forms.NumberInput(attrs={'class': 'form-control'}),
    #     'triggerPrice': forms.NumberInput(attrs={'class': 'form-control'}),
    #     'type': forms.Select(attrs={'class': 'form-control'}),
    #     'side': forms.Select(attrs={'class': 'form-control'}),
    #     'psnSide': forms.Select(attrs={'class': 'form-control'}),
    # }
    #
    # labels = {
    #     'qty': 'Количество монет',
    #     'price': 'Цена',
    #     'triggerPrice': 'Триггер цена',
    #     'type': 'Тип ордера',
    #     'side': 'Купить/Продать',
    #     'psnSide': 'Позиция',
    # }

    #  = {
    #     'qty': 'Используйте точку для обозначения дробной части',
    #     'price': 'Может не указываться для маркет ордеров',
    #     'triggerPrice': 'Цена срабатывания условного ордера. Оставьте пустым если используется не триггер ордер',
    #     # 'type': 'Тип ордера',
    #     # 'side': 'Купить/Продать',
    #     # 'psnSide': 'Позиция',
    # }
