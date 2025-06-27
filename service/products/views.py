from .models import Product, Category, Order
from .serializers import ProductSerializer, CategorySerializer, OrderSerializer, CreateOrderSerializer
from rest_framework import viewsets


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(available=True)
    serializer_class = ProductSerializer


class OrderViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)