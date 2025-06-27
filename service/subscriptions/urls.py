from django.db import router
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from subscriptions.views import TariffView, SubscriptionViewSet

app_name = "subscriptions"

router = DefaultRouter()
router.register(r'tariffs', TariffView, basename='tariffs')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('subscriptions/by-session/', SubscriptionViewSet.as_view({'get': 'by_session'}, ),
         name='subscription-by-session'),
    path('subscriptions/delete-sub/', SubscriptionViewSet.as_view({'delete': 'cancel_subscription'}, ), name='delete-subscription'),
path('subscriptions/my-subscriptions/', SubscriptionViewSet.as_view({'get': 'my_subscriptions'}),
         name='my-subscriptions'),
]