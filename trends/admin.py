from django.contrib import admin
from .models import Trend, SavedTrend, Subscription


@admin.register(Trend)
class TrendAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'platform', 'score', 'velocity', 'created_at']
    list_filter = ['category', 'platform', 'velocity']
    search_fields = ['title', 'description']
    ordering = ['-score']


@admin.register(SavedTrend)
class SavedTrendAdmin(admin.ModelAdmin):
    list_display = ['user', 'trend', 'saved_at']
    list_filter = ['saved_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_type', 'is_active', 'start_date', 'end_date']
    list_filter = ['plan_type', 'is_active']
