# django_tests_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers, permissions
from rest_framework.authtoken.views import obtain_auth_token
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib.auth import views as auth_views

router = routers.DefaultRouter()

schema_view = get_schema_view(
    openapi.Info(
        title="Calendar API",
        default_version='v1',
        description="API para plataforma educativa",
        contact=openapi.Contact(email="support@testeate.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Apps
    path('api/clases/', include('clases.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/users/', include('users.urls')),
    path('api/pagos/', include('pagos.urls')),
    path('api/chat/', include('chatRoom.urls')),
    
    # Auth
    path('accounts/', include('allauth.urls')),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api-token-auth/', obtain_auth_token),
    
    # Password reset
    path(
        'dj-rest-auth/password/reset/confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html'
        ),
        name='password_reset_confirm',
    ),
    
    # Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)