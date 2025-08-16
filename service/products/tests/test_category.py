from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import Category
from products.serializers import CategorySerializer
from subscriptions.models import CustomUser


class CategoryViewSetTest(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser1', password='testpass1')
        self.refresh = RefreshToken.for_user(self.user)
        self.category = Category.objects.create(name='Test Category 1')

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.refresh.access_token))

    def test_get_categories(self):
        self.authenticate()

        response = self.client.get('/api/v1/categories/')
        categories = Category.objects.all()
        serializer_data = CategorySerializer(categories, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer_data.data)

    def test_get_category_detail_authenticated(self):
        self.authenticate()
        response = self.client.get(f'/api/v1/categories/{self.category.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, CategorySerializer(self.category).data)

    def test_create_category_authenticated(self):
        self.authenticate()
        data = {'name': 'New Category(2)'}
        response = self.client.post('/api/v1/categories/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(Category.objects.last().name, 'New Category(2)')

    def test_update_category_authenticated(self):
        self.authenticate()
        data = {'name': 'Updated Category'}
        response = self.client.put(f'/api/v1/categories/{self.category.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated Category')

    def test_delete_category_authenticated(self):
        self.authenticate()
        response = self.client.delete(f'/api/v1/categories/{self.category.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)  # Проверяем, что категория удалена

    def test_get_categories_unauthenticated(self):
        response = self.client.get('/api/v1/categories/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
