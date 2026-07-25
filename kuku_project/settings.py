"""
Django settings for kuku_project
KUKU EVERYTHING - Tanzania's Chicken Marketplace
"""

from pathlib import Path
from decouple import config
from datetime import timedelta
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-kuku-everything-change-in-production-2025')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'accounts',
    'businesses',
    'orders',
    'reviews',
    'notifications',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kuku_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kuku_project.wsgi.application'

DATABASES = {
    'default': config(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR}/db.sqlite3',
        cast=dj_database_url.parse
    )
}


AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Dar_es_Salaam'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,https://kukueverythingtz.netlify.app'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# ════════════════════════════════════════════════════════════
# EMAIL - FREE via Gmail SMTP (500 emails/day free)
# ════════════════════════════════════════════════════════════
# STEP 1: Go to myaccount.google.com → Security → 2-Step Verification ON
# STEP 2: Search "App passwords" → Generate one for "Mail"
# STEP 3: Put that 16-char password as EMAIL_HOST_PASSWORD in .env
#
# In development (no .env set): emails print to console automatically
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST        = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT        = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS     = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER   = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='KUKU EVERYTHING <noreply@gmail.com>'
)

# ════════════════════════════════════════════════════════════
# SMS - FREE via Africa's Talking SANDBOX
# ════════════════════════════════════════════════════════════
# STEP 1: Register free at africastalking.com
# STEP 2: Use username='sandbox' and your sandbox API key
# STEP 3: In sandbox, SMS prints to AT simulator (no real SIM needed)
# STEP 4: To go live: switch username to your AT account name + get credits
#         (Africa's Talking Tanzania: ~TZS 25 per SMS)
#
# Alternative FREE option: Twilio trial gives $15 free credits (~100+ SMS)
# Set SMS_PROVIDER=twilio in .env and fill TWILIO_* vars below
#
SMS_PROVIDER = config('SMS_PROVIDER', default='beem')  # 'africastalking' | 'twilio' | 'console'

# Africa's Talking
AFRICASTALKING_USERNAME  = config('AFRICASTALKING_USERNAME', default='sandbox')
AFRICASTALKING_API_KEY   = config('AFRICASTALKING_API_KEY', default='')
AFRICASTALKING_SENDER_ID = config('AFRICASTALKING_SENDER_ID', default='')  # Leave blank in sandbox

# Twilio (alternative free trial option)
TWILIO_ACCOUNT_SID  = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN   = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_FROM_NUMBER  = config('TWILIO_FROM_NUMBER', default='')  # e.g. +12025551234

# ════════════════════════════════════════════════════════════
TANZANIA_REGIONS = [
    'Arusha', 'Dar es Salaam', 'Dodoma', 'Geita', 'Iringa',
    'Kagera', 'Katavi', 'Kigoma', 'Kilimanjaro', 'Lindi',
    'Manyara', 'Mara', 'Mbeya', 'Mjini Magharibi', 'Morogoro',
    'Mtwara', 'Mwanza', 'Njombe', 'Pemba Kaskazini', 'Pemba Kusini',
    'Pwani', 'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu',
    'Singida', 'Songwe', 'Tabora', 'Tanga', 'Unguja Kaskazini',
    'Unguja Kusini',
]

# ── Beem Africa SMS (Tanzania, ~TZS 18/SMS) ───────────────────
BEEM_API_KEY    = config('BEEM_API_KEY',    default='')
BEEM_SECRET_KEY = config('BEEM_SECRET_KEY', default='')
BEEM_SENDER_NAME = config('BEEM_SENDER_NAME', default='KUKU')
