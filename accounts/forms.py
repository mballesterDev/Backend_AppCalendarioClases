# accounts/forms.py

from dj_rest_auth.forms import AllAuthPasswordResetForm

def frontend_url_generator(request, user, temp_key):
    uid = user.pk
    token = temp_key
    # Aquí pones la URL de tu frontend (ajusta el dominio/puerto)
    return f"http://localhost:3000/password-reset-confirm/{uid}/{token}"

class CustomPasswordResetForm(AllAuthPasswordResetForm):
    def save(self, *args, **kwargs):
        kwargs['url_generator'] = frontend_url_generator
        return super().save(*args, **kwargs)
