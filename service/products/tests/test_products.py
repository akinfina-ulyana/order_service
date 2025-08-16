from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import Product
from products.serializers import ProductSerializer


class ProductViewSetTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser1', password='testpass')
        self.product1 = Product.objects.create(name="Product 1", available=True)
        self.product2 = Product.objects.create(name="Product 2", available=True)
        self.refresh = RefreshToken.for_user(self.user)

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.refresh.access_token))

    def test_get_products_authenticated(self):
        self.authenticate()
        response = self.client.get('/api/v1/products/')
        products = Product.objects.filter(available=True)
        serializer = ProductSerializer(products, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_product_detail_authenticated(self):
        self.authenticate()
        response = self.client.get(f'/api/v1/products/{self.product1.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, ProductSerializer(self.product1).data)

    def test_create_product_authenticated(self):
        self.authenticate()
        data = {'name': 'New Product', 'available': True}
        response = self.client.post('/api/v1/products/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 3)
        self.assertEqual(Product.objects.last().name, 'New Product')

    def test_update_product_authenticated(self):
        self.authenticate()
        data = {'name': 'Updated Product'}
        response = self.client.put(f'/api/v1/products/{self.product1.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product1.refresh_from_db()  # Обновляем объект из базы данных
        self.assertEqual(self.product1.name, 'Updated Product')

    def test_delete_product_authenticated(self):
        self.authenticate()
        response = self.client.delete(f'/api/v1/products/{self.product1.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 1)

    def test_get_products_unauthenticated(self):
        response = self.client.get('/api/v1/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)