from django.urls import resolve
from django.utils import timezone
from rest_framework.response import Response

class ActiveSubscriptionMiddleware:
    """Проверяем наличие активной подписки. Только для products url"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            resolved = resolve(request.path)
            app_name = resolved.app_name
        except:
            app_name = None

        # Если это не нужное приложение, пропускаем
        if app_name != "products":
            return self.get_response(request)

        # Проверка подписки
        if not request.user.is_anonymous:
            if not request.user.subscriptions.filter(is_active=True):
                return Response({'error': 'Подписка не активна, Для дальнейшего использования сервиса, пожалуйста зарегистрируйтесь'}, status=403)

        return self.get_response(request)

