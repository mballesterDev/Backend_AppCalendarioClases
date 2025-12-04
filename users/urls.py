from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    RegisterUserAPIView,
    get_countries,
    get_timezones,
    comprar_saldo_clases,  # NUEVO IMPORT
    user_profile, 
    custom_login,  # NUEVO IMPORT
    custom_logout   # NUEVO IMPORT
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('register/', RegisterUserAPIView.as_view(), name='register'),

    path('login/', custom_login, name='custom_login'),  # NUEVA RUTA
    path('logout/', custom_logout, name='custom_logout'),  # NUEVA RUTA

    path('countries/', get_countries, name='countries'),
    path('timezones/', get_timezones, name='timezones'),
    path('comprar_saldo/', comprar_saldo_clases, name='api_comprar_saldo'),  # NUEVA RUTA
    path('profile/', user_profile, name='user_profile'),
]

urlpatterns += router.urls