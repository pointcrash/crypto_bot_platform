from dj_rest_auth.serializers import PasswordResetSerializer
from django.conf import settings


class CustomPasswordResetSerializer(PasswordResetSerializer):
    def get_email_options(self):
        return {
            'email_template_name': 'templates/password_change_email.html',  # Укажите свой шаблон, если нужно
            'extra_email_context': {
                # 'custom_url': settings.CUSTOM_RESET_PASSWORD_URL,  # Например, кастомный URL из настроек
                'custom_url': "https://giga.com",  # Например, кастомный URL из настроек
            },
        }
