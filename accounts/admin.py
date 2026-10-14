from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'role',
        'phone_number',
        'is_staff',
        'is_active',
    )
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone_number')

    # Add custom fields to the user edit page
    fieldsets = UserAdmin.fieldsets + (
        (
            'Club Details',
            {'fields': ('role', 'phone_number')},
        ),
    )
    # Add custom fields to the user creation form
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'Club Details',
            {'fields': ('role', 'phone_number')},
        ),
    )
