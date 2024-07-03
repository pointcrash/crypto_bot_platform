from django.conf import settings
from django.http import HttpResponseRedirect


# Create your views here.
def password_reset_confirm_redirect(request, uidb64, token):
    return HttpResponseRedirect(
        f"http://localhost:3000/password-reset/confirm/{uidb64}/{token}/"
    )
