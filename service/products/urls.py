
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.views import CategoryViewSet, ProductViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'orders', OrderViewSet, basename='order')


urlpatterns = [
    path('', include(router.urls)),
]

