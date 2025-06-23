"""
Development settings for E-commerce API project.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database for development - SQLite yoki PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# SHU QISMNI O'ZGARTIRING - Development uchun PostgreSQL ishlatmoqchi bo'lsangiz
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': get_env_variable('DB_NAME', 'ecommerce_dev'),
#         'USER': get_env_variable('DB_USER', 'postgres'),
#         'PASSWORD': get_env_variable('DB_PASSWORD', 'password'),
#         'HOST': get_env_variable('DB_HOST', 'localhost'),
#         'PORT': get_env_variable('DB_PORT', '5432'),
#     }
# }

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",
    "http://localhost:8080",  # Vue development server
    "http://127.0.0.1:8080",
]

CORS_ALLOW_ALL_ORIGINS = True  # Only for development

# SMS Backend for development - Console backend
SMS_BACKEND = 'apps.sms.backends.console.ConsoleBackend'

# Redis settings for development - SHU QISMNI O'ZGARTIRING
REDIS_HOST = get_env_variable('REDIS_HOST', 'localhost')
REDIS_PORT = get_env_variable('REDIS_PORT', '6379')
REDIS_DB = get_env_variable('REDIS_DB', '1')  # Development uchun boshqa DB
REDIS_PASSWORD = get_env_variable('REDIS_PASSWORD', None)

REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Celery Configuration for development
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ALWAYS_EAGER = False  # Development uchun True qilish mumkin (async tasks synchronous bo'ladi)

# Cache configuration for development
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development-specific logging
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'

# Development tools
INSTALLED_APPS += [
    'django_extensions',  # Shell plus va boshqa development tools
    'debug_toolbar',      # Debug toolbar
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE

# Debug toolbar configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Development-specific settings
CELERY_TASK_ROUTES = {
    'apps.sms.tasks.send_sms': {'queue': 'sms'},
    'apps.sms.tasks.send_otp': {'queue': 'otp'},
}

# OTP settings for development - SHU QISMNI O'ZGARTIRING
OTP_SETTINGS.update({
    'EXPIRE_TIME': 600,  # 10 minutes for development
    'MAX_ATTEMPTS': 5,   # Ko'proq urinish development uchun
})

# JWT settings for development
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),  # Development uchun uzunroq
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
})