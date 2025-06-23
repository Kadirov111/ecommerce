"""
Celery configuration for E-commerce API project.
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('ecommerce_api')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule configuration
app.conf.beat_schedule = {
    'cleanup-expired-otps': {
        'task': 'apps.sms.tasks.cleanup_expired_otps',
        'schedule': 60.0,  # Har daqiqada cleanup
    },
}

app.conf.timezone = 'UTC'

# Task routing configuration
app.conf.task_routes = {
    'apps.sms.tasks.send_sms': {'queue': 'sms'},
    'apps.sms.tasks.send_otp': {'queue': 'otp'},
    'apps.orders.tasks.*': {'queue': 'orders'},
}

# Worker configuration
app.conf.worker_prefetch_multiplier = 1
app.conf.task_acks_late = True
app.conf.worker_max_tasks_per_child = 1000

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')