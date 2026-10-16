from django.contrib import admin
from .models import Trainer, GymSession


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'is_active', 'created_at')
    list_filter = ('is_active', 'specialty')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialty')


@admin.register(GymSession)
class GymSessionAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'trainer',
        'session_type',
        'starts_at',
        'ends_at',
        'max_capacity',
        'price',
        'status',
    )
    list_filter = ('session_type', 'status', 'trainer')
    search_fields = ('title', 'trainer__user__first_name', 'trainer__user__last_name')
    date_hierarchy = 'starts_at'
