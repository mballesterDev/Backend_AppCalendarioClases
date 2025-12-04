# accounts/urls.py

from django.urls import path
from .views import google_login

urlpatterns = [
    path('google-login/', google_login, name='google-login'),
]
