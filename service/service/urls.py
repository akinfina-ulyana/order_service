from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from subscriptions.views import UserRegistrationView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/register/', UserRegistrationView.as_view(), name='user-register'),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/v1/', include('subscriptions.urls')),
    path('api/v1/', include('products.urls')),
]
