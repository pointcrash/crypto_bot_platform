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
