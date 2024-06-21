from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import Account, WhiteListAccount


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'service', 'API_TOKEN', 'SECRET_KEY', 'is_mainnet', 'account_type', 'address',
                  'low_margin_value', 'low_margin_value_type', 'low_margin_actions', ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'}),
            'API_TOKEN': forms.TextInput(attrs={'class': 'form-control'}),
            'SECRET_KEY': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),

            'low_margin_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_margin_value_type': forms.Select(attrs={'class': 'form-control'}),
            'low_margin_actions': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Название аккаунта',
            'service': 'Биржа',
            'API_TOKEN': 'API Key',
            'SECRET_KEY': 'API Secret',
            'account_type': 'Тип аккаунта (только для ByBit)',
            'is_mainnet': 'Основная сеть',
            'address': 'Адрес USDT кошелька',

            'low_margin_value': 'Значение',
            'low_margin_value_type': 'Тип',
            'low_margin_actions': 'Действие',
        }


class RegistrationForm(UserCreationForm):
    secret_key = forms.CharField(label='Секретный ключ')

    class Meta:
        model = User
        fields = ('username', 'email', 'secret_key')

    def clean_secret_key(self):
        secret_key = self.cleaned_data.get('secret_key')

        if secret_key != 'k0o7gOtZNOsvYfqbEGSh':
            raise forms.ValidationError('Неверный ключ')

        return secret_key


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        exclude = ('password',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password' in self.fields:
            del self.fields['password']


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'password'}))


class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control', 'title': 'Расчет будет произведен от 00:00 выбранной даты'}), label='Дата начала')
    end_date = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control', 'title': 'За выбранную дату расчет произведен не будет'}), label='Дата окончания')


class AccountSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(AccountSelectForm, self).__init__(*args, **kwargs)
        self.fields['account'].required = False

        if user.is_superuser:
            user_accounts = Account.objects.all()
            account_choices = [('', '---------')]
            account_choices.extend([(account.id, account.name) for account in user_accounts])
            self.fields['account'].choices = account_choices
        else:
            user_accounts = Account.objects.filter(owner=user)
            account_choices = [('', '---------')]
            account_choices.extend([(account.id, account.name) for account in user_accounts])
            self.fields['account'].choices = account_choices

    account = forms.ChoiceField(
        choices=(),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )


class InternalTransferForm(forms.Form):
    ACCOUNT_TYPE_CHOICES = [
        ('FUND', 'Финансирования/Спот'),
        ('UNIFIED', 'Универсальный/Деривативный'),
    ]

    SYMBOL_CHOICES = [
        ('USDT', 'USDT'),
        ('BTC', 'BTC'),
        ('ETH', 'ETH'),
        ('SOL', 'SOL'),
    ]

    fromAccountType = forms.ChoiceField(choices=ACCOUNT_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), label='Откуда')
    toAccountType = forms.ChoiceField(choices=ACCOUNT_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), label='Куда')
    symbol = forms.ChoiceField(choices=SYMBOL_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), label='Монета')
    amount = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.NumberInput(attrs={'class': 'form-control'}), label='Количество')

    def clean(self):
        cleaned_data = super().clean()
        from_account_type = cleaned_data.get('fromAccountType')
        to_account_type = cleaned_data.get('toAccountType')

        if from_account_type == to_account_type:
            raise forms.ValidationError("Выберите разные типы аккаунтов")


class WithdrawForm(forms.Form):
    SYMBOL_CHOICES = [
        ('USDT', 'USDT'),
    ]

    CHAIN_TYPE_CHOICES = [
        ('TRX', 'TRC20 (Tron)'),
    ]
    chain = forms.ChoiceField(choices=CHAIN_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}), label='Сеть')
    symbol = forms.ChoiceField(choices=SYMBOL_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}), label='Монета')
    qty = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.NumberInput(attrs={'class': 'form-control'}), label='Количество')

    # def __init__(self, user, *args, **kwargs):
    #     super(WithdrawForm, self).__init__(*args, **kwargs)
    #     user_accounts = Account.objects.filter(owner=user)
    #     account_choices = [(acc.address, acc.name) for acc in user_accounts]
    #     self.fields['address'] = forms.ChoiceField(choices=account_choices, widget=forms.Select(attrs={'class': 'form-select'}), label='Адрес')


class WhiteListAccountForm(forms.ModelForm):
    class Meta:
        model = WhiteListAccount

        fields = ['address', 'note', 'symbol', 'chain']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'address': 'Адрес',
            'note': 'Заметка',
        }
