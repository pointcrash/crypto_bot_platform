import json

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.urls import reverse


class MyAccountAdapter(DefaultAccountAdapter):

    def get_email_confirmation_url(self, request, emailconfirmation):
        lang = "not_lang"

        if request.body:
            try:
                data = json.loads(request.body)
                lang = data.get("lang", lang)  # Если "lang" есть, берём его, иначе "ru"
            except json.JSONDecodeError:
                pass

        url = reverse("front_custom_confirm_email", args=[emailconfirmation.key])
        return f"{settings.FRONTEND_URL}/{lang}{url}"
