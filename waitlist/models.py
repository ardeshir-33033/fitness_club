from django.utils import timezone
from config import settings
from django.db import models



class WaitlistStatus(models.TextChoices):
  WAITING = 'WAITING', 'Waiting'  # در صف انتظار
  OFFERED = 'OFFERED', 'Offered'  # جایگاه به کاربر پیشنهاد شده
  CONVERTED = 'CONVERTED', 'Converted'  # نوبت خریداری و رزرو شد
  EXPIRED = 'EXPIRED', 'Expired'  # مهلت خرید منقضی شد
  CANCELLED = 'CANCELLED', 'Cancelled'  # انصراف کاربر



class Waitlist(models.Model):
    user  = models.ForeignKey(settings.AUTH_USER_MODEL,
     on_delete=models.CASCADE, related_name="waitlist_users")
    session = models.ForeignKey(
        'gym_sessions.GymSession',
        on_delete=models.CASCADE,
        related_name="waitlist_sessions",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    offered_at = models.DateTimeField(null=True, blank=True)
    offered_expires_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(
      max_length=20,
      choices=WaitlistStatus.choices,
      default=WaitlistStatus.WAITING,
    )

    class Meta:
        ordering = ['joined_at']
        constraints = [
        # هر کاربر فقط یک‌بار می‌تواند در وضعیت فعال صف یک سانس باشد
        models.UniqueConstraint(
            fields=['user', 'session'],
            condition=models.Q(
                status__in=[WaitlistStatus.WAITING, WaitlistStatus.OFFERED]
            ),
            name='unique_active_waitlist_per_user_session',
        )
    ]

    def __str__(self):
        return f'Waitlist #{self.id} - {self.user.username} for {self.session.title} [{self.get_status_display()}]'                


    @property
    def is_offer_expired(self) -> bool:
        """بررسی اینکه آیا مهلت ۱۰ دقیقه‌ای خرید سانس سپری شده است یا خیر"""
        return (
            self.status == WaitlistStatus.OFFERED
            and self.offered_expires_at is not None
            and timezone.now() > self.offered_expires_at
        )    