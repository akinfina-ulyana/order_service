from django.contrib import admin

from django.contrib import admin
from .models import Tariff, UserSubscription, CustomUser

from django.contrib.auth import get_user_model

User = get_user_model()

admin.site.register(CustomUser)

@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    read_only_fields = ('price',)
    list_display = ('name', 'duration_days', 'price', 'is_active')
    list_editable = ('price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tariff', 'start_date', 'end_date', 'is_active', 'auto_renewal')
    list_filter = ('is_active', 'tariff', 'auto_renewal')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('start_date', 'end_date')
    date_hierarchy = 'end_date'