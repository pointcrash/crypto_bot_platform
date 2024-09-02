from dj_rest_auth.views import LoginView
from django.conf import settings
from django.http import HttpResponseRedirect

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
