# settings.py completo CON TODO LO QUE TENÍAS, solo corrigiendo AUTHENTICATION_BACKENDS
from pathlib import Path
import os
from dotenv import load_dotenv
from accounts.utils import custom_password_reset_confirm_url

# Cargar variables de entorno
load_dotenv()

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
DJRESTAUTH_RESET_PASSWORD_CONFIRM_URL = custom_password_reset_confirm_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-o!h@8uz_tbtwvk86c7lp_w@=98)77j#2npb4ng%v7ygcmx+u6r')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# ALLOWED_HOSTS
allowed_hosts_str = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,.ngrok-free.app')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(',')]

# Application definition
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Terceros
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'corsheaders',
    'crispy_forms',
    'crispy_tailwind',
    'drf_yasg',

    # Tus apps
    'users',
    'accounts',
    'clases', 
    'chatRoom',
    'pagos',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = 'django_tests_backend.urls'

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'ngrok-skip-browser-warning',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
            ],
        },
    },
]

WSGI_APPLICATION = 'django_tests_backend.wsgi.application'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

FRONTEND_URL = os.getenv('FRONTEND_URL', "http://localhost:5173")

REST_AUTH = {
    'LOGIN_SERIALIZER': 'dj_rest_auth.serializers.LoginSerializer',
    'TOKEN_SERIALIZER': 'dj_rest_auth.serializers.TokenSerializer',
    'JWT_SERIALIZER': 'dj_rest_auth.serializers.JWTSerializer',
    'USER_DETAILS_SERIALIZER': 'users.serializers.UserProfileSerializer',
    'USE_JWT': False,
    'JWT_AUTH_COOKIE': None,
    'JWT_AUTH_REFRESH_COOKIE': None,
    'SESSION_LOGIN': False,
}

DJANGO_REST_AUTH = {
    'PASSWORD_RESET_CONFIRM_URL': 'password-reset-confirm/{uid}/{token}',
}

REST_AUTH_SERIALIZERS = {
    'PASSWORD_RESET_SERIALIZER': 'dj_rest_auth.serializers.PasswordResetSerializer',
    'USER_DETAILS_SERIALIZER': 'users.CustomUserDetailsSerializer'
}

REST_AUTH_FORMS = {
    'PASSWORD_RESET_FORM': 'passwordReset.CustomPasswordResetForm',
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# PUSHER
PUSHER_APP_ID = os.getenv('PUSHER_APP_ID', '2076756')
PUSHER_KEY = os.getenv('PUSHER_KEY', 'c0fc8ce24c06ebef7a64')
PUSHER_SECRET = os.getenv('PUSHER_SECRET', 'c7bbfe6fa96d53fbe153')
PUSHER_CLUSTER = os.getenv('PUSHER_CLUSTER', 'eu')

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://e4d23a237583.ngrok-free.app",
    "https://de22a4aeb64a.ngrok-free.app",
]

CORS_ALLOW_CREDENTIALS = True

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = int(os.getenv('SITE_ID', 1))

ACCOUNT_SIGNUP_FIELDS = ['username*', 'email*', 'password1*', 'password2*']
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_UNIQUE_EMAIL = True
AUTH_USER_MODEL = 'users.CustomUser'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'

REST_AUTH_REGISTER_SERIALIZERS = {
    'REGISTER_SERIALIZER': 'users.serializers.CustomRegisterSerializer',
}

REST_AUTH_SERIALIZERS = {
    "PASSWORD_RESET_SERIALIZER": "accounts.serializers.MyPasswordResetSerializer"
}

HEADLESS_ONLY = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "https://de22a4aeb64a.ngrok-free.app",
    "https://manelteacherinfo.pythonanywhere.com",
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'APP': {
            'client_id': os.getenv('SOCIALACCOUNT_GOOGLE_CLIENT_ID', '123'),
            'secret': os.getenv('SOCIALACCOUNT_GOOGLE_CLIENT_SECRET', '456'),
            'key': ''
        }
    }
}

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

# Crispy forms pero de tailwind
CRISPY_ALLOWED_TEMPLATE_PACKS = ["tailwind"]
CRISPY_TEMPLATE_PACK = "tailwind"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# All auth gmail
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'manelteacherinfo@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Manel Ballester Teacher info')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'

# STRIPE
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Configuración para producción (sobrescribe en producción)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True