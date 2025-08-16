from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import Order, Category, Product
from products.serializers import CreateOrderSerializer, OrderSerializer


class OrderViewSetTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.refresh = RefreshToken.for_user(self.user)
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            price=22.22,
            category=self.category,
            description='Test Description',
            available=True
        )

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.refresh.access_token))

    def test_get_orders_authenticated(self):
        self.authenticate()
        response = self.client.get('/api/v1/orders/')
        orders = Order.objects.filter(user=self.user)
        serializer = OrderSerializer(orders, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_order_authenticated(self):
        self.authenticate()
        data = {
            'items': [
                {'product': self.product.id, 'quantity': 2, 'price': self.product.price}
            ]
        }
        response = self.client.post('/api/v1/orders/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

        created_order = Order.objects.last()
        self.assertEqual(created_order.items.count(), 1)
        self.assertEqual(created_order.items.first().product, self.product)

    def test_get_order_detail_authenticated(self):
        self.authenticate()
        order = Order.objects.create(user=self.user, paid=False)
        OrderItem.objects.create(order=order, product=self.product, price=self.product.price, quantity=1)

        response = self.client.get(f'/api/v1/orders/{order.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, OrderSerializer(order).data)

    def test_create_order_unauthenticated(self):
        data = {
            'items': [
                {'product': self.product.id, 'quantity': 1, 'price': self.product.price}
            ]
        }
        response = self.client.post('/api/v1/orders/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_orders_unauthenticated(self):
        response = self.client.get('/api/v1/orders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)