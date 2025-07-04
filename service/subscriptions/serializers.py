from datetime import timedelta
from email.policy import default

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from subscriptions.models import Tariff, UserSubscription
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    phone = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'phone']

    def validate(self, attrs):  # Вызывается автоматически при is_valid()
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(username=validated_data['username'], email=validated_data['email'], phone=validated_data['phone'])
        user.set_password(validated_data['password'])
        user.save()
        return user


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = ['id', 'name', 'duration_days', 'price', 'description']


class SubscriptionSerializer(serializers.ModelSerializer):
    tariff = TariffSerializer(read_only=True)  # Вложение информации о тарифе

    class Meta:
        model = UserSubscription
        fields = ['id', 'user', 'tariff', 'tariff_id', 'start_date',
                  'end_date', 'is_active', 'auto_renewal', 'payment_status']
        read_only_fields = ['id', 'user', 'start_date', 'end_date', 'is_active', 'payment_status']

        def validate(self, attrs):
            # сериализатор имеет доступ к текущему запросу (request) через self.context
            user = self.context['request'].user
            tariff = attrs.get('tariff')
            if UserSubscription.objects.filter(user=user, is_active=True, end_date__gte=timezone.now()).exists():
                raise ValidationError('У вас есть активная подписка')
            return attrs



class SubscriptionWithTariffSerializer(serializers.ModelSerializer):
    tariff_name = serializers.CharField(source='tariff.name')
    tariff_description = serializers.CharField(source='tariff.description')
    tariff_price = serializers.DecimalField(
        source='tariff.price',
        max_digits=10,
        decimal_places=2
    )
    tariff_days = serializers.IntegerField(source='tariff.duration_days')

    class Meta:
        model = UserSubscription
        fields = [
            'is_active',
            'tariff_days',
            'tariff_name',
            'tariff_description',
            'tariff_price',
        ]
