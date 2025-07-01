from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    phone = models.CharField(max_length=13, blank=True, verbose_name="Номер телефона")
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True, verbose_name="ID пользователя")
    chat_id = models.BigIntegerField(null=True, blank=True, unique=True, verbose_name="ID чата с пользователем")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.username}/{self.phone}"

class Tariff(models.Model):
    """ Модель описания тарифов(на 1 месяц, на 3 месяца, на 6 месяцев и на год)"""
    name = models.CharField(max_length=240, blank=False, verbose_name="Название тарифа")
    is_active = models.BooleanField(default=True, verbose_name="Активный тариф", help_text="Доступен ли тариф для покупки")
    duration_days = models.PositiveIntegerField(verbose_name="Длительность (дни)", help_text="Сколько дней действует подписка")
    description = models.TextField(verbose_name="Описание тарифа", blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Цена", null=False)
    stripe_price_id = models.CharField(max_length=100, blank=False, verbose_name="ID цены в Stripe")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"

    def __str__(self):
        return f"{self.name} - {self.price} руб."


class UserSubscription(models.Model):
    """Модель подписки пользователя"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачено'),
        ('failed', 'Отменено'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions', verbose_name="Пользователь")
    tariff = models.ForeignKey(Tariff, on_delete=models.PROTECT, related_name='subscriptions', verbose_name="Тариф")
    start_date = models.DateTimeField(default=timezone.now, verbose_name="Дата начала")
    end_date = models.DateTimeField(verbose_name="Дата окончания")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    auto_renewal = models.BooleanField(default=False, verbose_name="Автопродление")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="Статус оплаты")
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID после создания сессии")
    # payment_data = models.JSONField(default=dict, blank=True, verbose_name="Данные платежа")

    class Meta:
        verbose_name = "Подписка пользователя"
        verbose_name_plural = "Подписки пользователей"
        ordering = ['-start_date']


    def __str__(self):
        return f"Подписка {self.user.email} ({self.tariff.name}) до {self.end_date.strftime('%d.%m.%Y')}"

    def save(self, *args, **kwargs):
        """Автоматический расчёт end_date при создании"""
        if not self.end_date and self.tariff:
            self.end_date = self.start_date + timedelta(days=self.tariff.duration_days)
        super().save(*args, **kwargs)

    @property
    def days_remaining(self):
        """Оставшееся количество дней подписки"""
        return (self.end_date - timezone.now()).days if self.is_active else 0






