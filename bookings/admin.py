from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'session',
        'status',
        'created_at',
        'expires_at',
        'confirmed_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'session__title', 'idempotency_key')
    readonly_fields = ('created_at',)
