"""
Production settings for E-commerce API project.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SHU QISMNI O'ZGARTIRING - Production domainlaringizni qo'shing
ALLOWED_HOSTS = [
    get_env_variable('ALLOWED_HOST', 'api.example.com'),
    'your-domain.com',
    'www.your-domain.com',
]

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Database configuration for production - SHU QISMNI O'ZGARTIRING
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env_variable('DB_NAME'),
        'USER': get_env_variable('DB_USER'),
        'PASSWORD': get_env_variable('DB_PASSWORD'),
        'HOST': get_env_variable('DB_HOST'),
        'PORT': get_env_variable('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Redis Configuration for production - SHU QISMNI O'ZGARTIRING
REDIS_HOST = get_env_variable('REDIS_HOST')
REDIS_PORT = get_env_variable('REDIS_PORT', '6379')
REDIS_DB = get_env_variable('REDIS_DB', '0')
REDIS_PASSWORD = get_env_variable('REDIS_PASSWORD')

REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Celery Configuration for production
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_MAX_TASKS_PER_CHILD = 1000

# Cache configuration for production
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
                'ssl_cert_reqs': None,
            }
        }
    }
}

# SMS Backend for production - SHU QISMNI O'ZGARTIRING (qaysi SMS provideringizni tanlang)
SMS_BACKEND = 'apps.sms.backends.eskiz.EskizBackend'  # yoki 'apps.sms.backends.playmobile.PlaymobileBackend'

# Email configuration for production - SHU QISMNI O'ZGARTIRING
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = get_env_variable('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = get_env_variable('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_env_variable('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = get_env_variable('DEFAULT_FROM_EMAIL', 'noreply@example.com')

# Static files configuration for production
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files configuration for production
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# AWS S3 configuration (agar S3 ishlatmoqchi bo'lsangiz) - SHU QISMNI O'ZGARTIRING
# AWS_ACCESS_KEY_ID = get_env_variable('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = get_env_variable('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = get_env_variable('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = get_env_variable('AWS_S3_REGION_NAME', 'us-east-1')
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
# AWS_DEFAULT_ACL = 'public-read'
# AWS_S3_OBJECT_PARAMETERS = {
#     'CacheControl': 'max-age=86400',
# }
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# CORS settings for production - SHU QISMNI O'ZGARTIRING
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
    "https://www.your-frontend-domain.com",
]

CORS_ALLOW_CREDENTIALS = True

# Production logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/django.log',  # SHU QISMNI O'ZGARTIRING
            'maxBytes': 15728640,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/django_error.log',  # SHU QISMNI O'ZGARTIRING
            'maxBytes': 15728640,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Admin email for error notifications - SHU QISMNI O'ZGARTIRING
ADMINS = [
    ('Admin', get_env_variable('ADMIN_EMAIL', 'admin@example.com')),
]

MANAGERS = ADMINS

# Session configuration for production
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True

# CSRF configuration for production
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_USE_SESSIONS = True

# Celery task routing for production
CELERY_TASK_ROUTES = {
    'apps.sms.tasks.send_sms': {'queue': 'sms'},
    'apps.sms.tasks.send_otp': {'queue': 'otp'},
    'apps.orders.tasks.process_order': {'queue': 'orders'},
    'apps.orders.tasks.send_order_confirmation': {'queue': 'notifications'},
}

# Celery beat schedule for periodic tasks
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-otps': {
        'task': 'apps.sms.tasks.cleanup_expired_otps',
        'schedule': crontab(minute=0),  # Har soat
    },
    'cleanup-expired-sessions': {
        'task': 'apps.authentication.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # Har kuni soat 2:00 da
    },
}