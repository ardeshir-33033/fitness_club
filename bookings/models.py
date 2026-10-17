from gym_sessions.models import GymSession
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
class BookingStatus(models.TextChoices):
    HELD = 'HELD', 'Held'               # 10-minute temporary lock
    CONFIRMED = 'CONFIRMED', 'Confirmed' # Paid & finalized
    CANCELLED = 'CANCELLED', 'Cancelled' # Cancelled by user/admin
    EXPIRED = 'EXPIRED', 'Expired'       # Hold timed out


class Booking(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    session = models.ForeignKey(
        GymSession,
        # 'gym_sessions.GymSession',
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.HELD,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="Deadline for completing payment (created_at + 10 mins)",
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when payment was confirmed",
    )    
    idempotency_key = models.CharField(
        max_length=120,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique key from mobile client to prevent double submissions",
    )    

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # Business Rule: A client cannot have more than ONE active booking (HELD or CONFIRMED)
            # for the exact same session at the same time.
            models.UniqueConstraint(
                fields=['user', 'session'],
                condition=models.Q(status__in=[BookingStatus.HELD, BookingStatus.CONFIRMED]),
                name='unique_active_booking_per_user_session',
            )
        ]    
    def __str__(self):
        return f"Booking #{self.id} - {self.user.username} for {self.session.title} [{self.get_status_display()}]"     

    def save(self, *args, **kwargs):
        # Automatically set a 10-minute expiration when a new HELD booking is created
        if not self.expires_at and self.status == BookingStatus.HELD:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    @property
    def is_hold_expired(self) -> bool:
        """Checks if a temporary hold has passed its 10-minute window."""
        return self.status == BookingStatus.HELD and timezone.now() > self.expires_at                  