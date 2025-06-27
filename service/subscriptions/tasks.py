# subscriptions/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import UserSubscription
import logging

logger = logging.getLogger(__name__)


@shared_task
def deactivate_expired_subscriptions():
    """Ежедневная задача для деактивации просроченных подписок"""
    try:
        expired_subs = UserSubscription.objects.filter(
            is_active=True,
            end_date__lt=timezone.now()  # Подписки с end_date в прошлом
        )

        count = expired_subs.count()
        expired_subs.update(is_active=False, payment_status='expired')

        logger.info(f"Deactivated {count} expired subscriptions")
        return f"Deactivated {count} subscriptions"

    except Exception as e:
        logger.error(f"Error deactivating subscriptions: {str(e)}")
        raise