from django.contrib import admin
from .models import Waitlist


@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'user',
      'session',
      'status',
      'joined_at',
      'offered_at',
      'offered_expires_at',
  )
  list_filter = ('status', 'joined_at')
  search_fields = (
      'user__username',
      'user__first_name',
      'user__last_name',
      'session__title',
  )
  readonly_fields = ('joined_at',)
