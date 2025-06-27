from celery import Celery
from celery.schedules import crontab
from django.conf import settings
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'service.settings')

app = Celery('order_service')

# Более чистая конфигурация
app.config_from_object('django.conf:settings', namespace='CELERY')

# Настройки подключения к брокеру
app.conf.update(
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10, 
    broker_connection_timeout=30,
    broker_transport_options={
        'visibility_timeout': 3600,
        'socket_connect_timeout': 30,
        'retry_policy': {
            'interval_start': 0,
            'interval_step': 0.2,
            'interval_max': 0.5,
            'max_retries': 10
        }
    }
)

# Планировщик задач
app.conf.beat_schedule = {
    'deactivate-expired-subscriptions': {
        'task': 'subscriptions.tasks.deactivate_expired_subscriptions',
        'schedule': crontab(hour=2, minute=0),
    },
}

app.autodiscover_tasks()