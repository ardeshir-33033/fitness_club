from django.conf import settings
from django.db import models

class Trainer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trainer_profile',
        limit_choices_to={'role': 'TRAINER'},
        help_text="User account with TRAINER role",
    )
    specialty = models.CharField(
        max_length=120,
        help_text="e.g. Strength & Conditioning, CrossFit" )   
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this trainer is currently taking sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"Coach {self.user.get_full_name() or self.user.username} ({self.specialty})"

class GymSession(models.Model):

    class SessionType(models.TextChoices):
        PRIVATE_1ON1 = 'PRIVATE_1ON1', 'Private 1-on-1'
        GROUP_CLASS = 'GROUP_CLASS', 'Group Class'

    class SessionStatus(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'

    trainer = models.ForeignKey(
        Trainer,
        on_delete=models.PROTECT,
        related_name='sessions',
        help_text="Trainer conducting the session",
    )
    title = models.CharField(
        max_length=200,
        help_text="Session title"
    )
    description = models.TextField(
        blank=True,
        help_text="Session description"
    )
        
    session_type = models.CharField(
        max_length=20,
        choices=SessionType.choices,
        default=SessionType.GROUP_CLASS,
    )
    # starts_at = models.DateTimeField(db_index=True)    
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    max_capacity = models.PositiveIntegerField(
        help_text="Maximum allowed attendees (1 for private, up to 20 for group)",
    )    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Cost per booking in standard currency units",
    )    
    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.SCHEDULED,
    )    
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['starts_at']
        # indexes = [
        #     # Composite index for Sunday 8 PM schedule lookups:
        #     models.Index(fields=['starts_at', 'status'], name='idx_session_schedule'),
        # ]
        constraints = [
            # 1. Database constraint: A session cannot end before or at the start time
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F('starts_at')),
                name='session_ends_after_starts',
            ),
            # 2. Database constraint: Capacity must be at least 1
            models.CheckConstraint(
                condition=models.Q(max_capacity__gt=0),
                name='session_capacity_positive',
            ),
            # 3. Database constraint: Price cannot be negative
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name='session_price_non_negative',
            ),
        ]
    def __str__(self):
        return f"{self.title} - {self.starts_at:%Y-%m-%d %H:%M} ({self.get_session_type_display()})"
    @property
    def is_private(self) -> bool:
        return self.session_type == self.SessionType.PRIVATE_1ON1
