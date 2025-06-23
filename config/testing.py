"""
Testing settings for E-commerce API project.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Database for testing - In-memory SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Password hashers for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Cache configuration for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# SMS Backend for testing
SMS_BACKEND = 'apps.sms.backends.console.ConsoleBackend'

# Celery configuration for testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'


# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Media files for testing
MEDIA_ROOT = '/tmp/media_test'

# OTP settings for testing
OTP_SETTINGS = {
    'LENGTH': 6,
    'EXPIRE_TIME': 300,  # 5 minutes
    'CACHE_PREFIX': 'test_otp_',
    'MAX_ATTEMPTS': 3,
    'RESEND_COOLDOWN': 60,
}

# JWT settings for testing
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=1),
})

# Logging for testing
LOGGING_CONFIG = None
import logging

logging.disable(logging.CRITICAL)