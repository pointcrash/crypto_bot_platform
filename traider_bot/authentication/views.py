from dj_rest_auth.views import LoginView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from django.shortcuts import get_object_or_404

from django.http import HttpResponseRedirect
from rest_framework.views import APIView

from main.serializers import UserSerializer


# Create your views here.
def password_reset_confirm_redirect(request, uidb64, token):
    return HttpResponseRedirect(
        f"http://localhost:3000/password-reset/confirm/{uidb64}/{token}/"
    )


class CustomLoginView(LoginView):
    def get_response(self):
        original_response = super().get_response()
        user_data = UserSerializer(self.user, many=False).data
        if 'user' in original_response.data:
            original_response.data['user'].update(user_data)
        else:
            original_response.data['user'] = user_data

        return original_response


class ConfirmEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, key, *args, **kwargs):
        confirmation = None
        try:
            confirmation = EmailConfirmationHMAC.from_key(key)
        except EmailConfirmation.DoesNotExist:
            confirmation = get_object_or_404(EmailConfirmation, key=key)

        if confirmation:
            confirmation.confirm(request)
            return Response({'detail': 'Email confirmed successfully'}, status=status.HTTP_200_OK)

        return Response({'detail': 'Invalid or expired key'}, status=status.HTTP_400_BAD_REQUEST)
