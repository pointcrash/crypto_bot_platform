import json

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.urls import reverse


class MyAccountAdapter(DefaultAccountAdapter):

    def get_email_confirmation_url(self, request, emailconfirmation):
        lang = request.data.get("lang", "sddsg")
        print(lang)

        url = reverse("front_custom_confirm_email", args=[emailconfirmation.key])
        return f"{settings.FRONTEND_URL}/{lang}{url}"
