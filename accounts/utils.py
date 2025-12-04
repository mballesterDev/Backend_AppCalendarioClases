from django.conf import settings

def custom_password_reset_confirm_url(user, token):
    uid = user.pk
    return f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
