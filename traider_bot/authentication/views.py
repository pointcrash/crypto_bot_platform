from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from django.shortcuts import get_object_or_404

from django.http import HttpResponseRedirect, JsonResponse
from rest_framework.views import APIView

from main.models import Referral
from main.serializers import UserSerializer, ReferralSerializer


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


class CustomRegisterView(RegisterView):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = self.perform_create(serializer)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

        headers = self.get_success_headers(serializer.data)
        data = self.get_response_data(user)

        if data:
            response = Response(
                data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        else:
            response = Response(status=status.HTTP_204_NO_CONTENT, headers=headers)

        return response

    def perform_create(self, serializer):
        user = super().perform_create(serializer)
        self.add_to_referrals(user)
        return user

    def add_to_referrals(self, user):
        ref_code = self.request.data.get('ref_code')
        if not ref_code:
            return

        try:
            referral = Referral.objects.get(code=ref_code)
        except Referral.DoesNotExist:
            user.delete()
            raise Exception('Referral code does not exist')

        referral.referred_users.add(user)
        referral.save()
        return
