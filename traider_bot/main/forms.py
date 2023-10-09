from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'API_TOKEN', 'SECRET_KEY', 'is_mainnet', 'account_type', ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'API_TOKEN': forms.TextInput(attrs={'class': 'form-control'}),
            'SECRET_KEY': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Name',
            'API_TOKEN': 'API TOKEN',
            'SECRET_KEY': 'SECRET KEY',
            'account_type': 'ACCOUNT TYPE',
            'is_mainnet': 'IS MAINNET',
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


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'password'}))


class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control', 'title': 'Расчет будет произведен от 00:00 выбранной даты'}))
    end_date = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control', 'title': 'За выбранную дату расчет произведен не будет'}))


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

