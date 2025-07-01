from datetime import datetime
from venv import logger

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet

from subscriptions.models import Tariff, UserSubscription
from subscriptions.serializers import (TariffSerializer, UserRegistrationSerializer, SubscriptionSerializer,
                                       SubscriptionWithTariffSerializer, )
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.decorators import action
from django.conf import settings
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
import stripe
from django.contrib.auth import get_user_model

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY
success_url = f'{settings.FRONTEND_URL}/success/?session_id={{CHECKOUT_SESSION_ID}}',
cancel_url = f'{settings.FRONTEND_URL}/cancel/'


class UserRegistrationView(CreateAPIView):
    # Формальность, запрос не выполняется
    queryset = User.objects.all()  # просто нужно так как это требует родитель CreateAPIView(т.е. GenericAPIView)
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer_data = self.get_serializer(data=request.data)
        serializer_data.is_valid(raise_exception=True)
        user = serializer_data.save()

        # Генерация JWT токенов
        refresh = RefreshToken.for_user(user)

        return Response({
            "user": serializer_data.data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "detail": "Регистрация прошла успешно. "
                      "Пожалуйста пройдите по адресу http://127.0.0.1:8000/api/v1/create_subscription/ для приобретения подписки"
        }, status=status.HTTP_201_CREATED)


class TariffView(ReadOnlyModelViewSet):
    """ Представление для получения списка всех активных тарифов и одного тарифа. Доступно без аутентификации """
    permission_classes = [AllowAny]

    queryset = Tariff.objects.filter(is_active=True)
    serializer_class = TariffSerializer


class SubscriptionViewSet(ViewSet):

    # Создание сессии оплаты в Stripe
    @csrf_exempt
    @action(detail=False, methods=['POST'])
    def create_checkout_session(self, request):
        user = request.user
        tariff_id = request.data.get('tariff_id')

        if not tariff_id:
            return Response({'error': 'tariff_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tariff = Tariff.objects.get(id=tariff_id, is_active=True)

            # Создаем подписку в статусе "ожидает оплаты"
            subscription = UserSubscription.objects.create(user=user, tariff=tariff, start_date=timezone.now(),
                                                           is_active=False, payment_status='pending')

            # Создаем сессию оплаты в Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': tariff.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f'{settings.FRONTEND_URL}/api/v1/subscriptions/by_session/?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'{settings.FRONTEND_URL}/api/v1/subscriptions/canceled/',
                metadata={
                    'user_id': user.id,
                    'subscription_id': subscription.id,
                    'tariff_id': tariff.id
                }
            )
            session = stripe.checkout.Session.retrieve(checkout_session.id)
            subscription.stripe_subscription_id = session.subscription
            subscription.save()
            subscription.refresh_from_db()

            return Response({'session_id': checkout_session.id, 'url': checkout_session.url})

        except Tariff.DoesNotExist:
            return Response({'error': 'Tariff not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Обработка успешной оплаты (для вебхука)
    @csrf_exempt
    @action(detail=False, methods=['POST'])
    def webhook(self, request):
        payload = request.body
        sig_header = request.headers.get('Stripe-Signature')  # ('Stripe-Signature')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except stripe.error.SignatureVerificationError as e:
            return Response({'error': str(e)}, status=400)

            # Обработка успешной оплаты
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            if session.payment_status == 'paid':
                self._handle_successful_payment(session)
        elif event['type'] == 'invoice.paid':
            # Обновляем подписку при регулярных платежах
            invoice = event['data']['object']
            self._handle_invoice_paid(invoice)
        elif event['type'] == 'invoice.payment_failed':
            # Деактивируем подписку при неудачном платеже
            invoice = event['data']['object']
            self._handle_payment_failed(invoice)

        return Response(status=200)

    def _handle_successful_payment(self, session):
        """Обработка успешного платежа (вызывается из checkout.session.completed)"""
        try:

            subscription = UserSubscription.objects.get(
                id=session.metadata['subscription_id']
            )
            stripe_session = stripe.checkout.Session.retrieve(session.id)
            subscription.is_active = True
            subscription.payment_status = 'paid'
            subscription.stripe_subscription_id = stripe_session.subscription
            subscription.save()
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")

    @csrf_exempt
    @action(detail=False, methods=['GET'])
    def by_session(self, request):
        """Обработчик для проверки статуса по session_id"""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'session_id is required'}, status=400)

        try:
            # Проверяем сессию в Stripe
            session = stripe.checkout.Session.retrieve(session_id)

            # Получаем подписку
            subscription = UserSubscription.objects.get(
                id=session.metadata['subscription_id']
            )

            # Дополнительная проверка платежа
            if session.payment_status != 'paid':
                return Response({'status': 'unpaid'}, status=402)

            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data)

        except UserSubscription.DoesNotExist:
            return Response({'error': 'Subscription not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    def _handle_invoice_paid(self, invoice):
        """Обработка регулярных платежей подписки"""
        try:
            subscription = UserSubscription.objects.get(
                stripe_subscription_id=invoice['subscription']
            )
            subscription.payment_status = 'paid'
            subscription.current_period_end = datetime.fromtimestamp(
                invoice['lines']['data'][0]['period']['end']
            )
            subscription.save()
        except Exception as e:
            logger.error(f"Invoice processing error: {str(e)}")

    def _handle_payment_failed(self, invoice):
        subscription_id = invoice['subscription']
        UserSubscription.objects.filter(
            stripe_subscription_id=subscription_id
        ).update(
            payment_status='failed',
            is_active=False
        )

    @action(detail=False, methods=['GET'])
    def my_subscriptions(self, request):
        """Получение подписок текущего пользователя с данными тарифов"""
        if request.user.is_anonymous:
            return Response(
                {"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        subscriptions = UserSubscription.objects.filter(
            user=request.user
        ).select_related('tariff')

        serializer = SubscriptionWithTariffSerializer(subscriptions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['DELETE'])
    def cancel_subscription(self, request):
        """Метод для отмены активной подписки по запросу пользователя"""
        user = request.user

        try:
            # Находим активную подписку пользователя
            subscription = UserSubscription.objects.get(
                user=user,
                is_active=True,
                payment_status='paid'
            )

            if not subscription.stripe_subscription_id:
                return Response(
                    {'error': 'Subscription has no Stripe ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                # Отменяем подписку в Stripe
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )

                # Обновляем статус в базе
                subscription.auto_renewal = False
                subscription.is_active = False
                subscription.save()

                return Response(
                    {'status': 'Subscription will be canceled at the end of the current period'},
                    status=status.HTTP_200_OK
                )

            except stripe.error.StripeError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except UserSubscription.DoesNotExist:
            return Response(
                {'error': 'Active subscription not found'},
                status=status.HTTP_404_NOT_FOUND
            )



