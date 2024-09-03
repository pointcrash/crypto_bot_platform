from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.urls import reverse


class MyAccountAdapter(DefaultAccountAdapter):

    def get_email_confirmation_url(self, request, emailconfirmation):
        url = reverse("account_confirm_email", args=[emailconfirmation.key])
        return f"{settings.FRONTEND_URL}{url}"
