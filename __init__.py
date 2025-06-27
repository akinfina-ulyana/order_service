from service.celery import app as celery_app

__all__ = ('celery_app', ) # чтобы стартануло вместе с моим приложением
