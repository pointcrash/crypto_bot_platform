import json

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.urls import reverse
from django.utils.translation import get_language_from_request


class MyAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        user_language = get_language_from_request(request)

        url = reverse("front_custom_confirm_email", args=[emailconfirmation.key])
        return f"{settings.FRONTEND_URL}/{user_language}{url}"
