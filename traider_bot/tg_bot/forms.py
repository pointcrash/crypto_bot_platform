from django import forms
from tg_bot.models import TelegramAccount


class TelegramAccountForm(forms.ModelForm):
    class Meta:
        model = TelegramAccount
        fields = ['telegram_username', ]
        widgets = {
            'telegram_username': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'telegram_username': 'Enter username in telegram',
        }
