from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    """
    TextChoices provides typed, clean enums in Django models.
    Stored in PostgreSQL as VARCHAR(10).
    """
    CLIENT = 'CLIENT', 'Client'
    TRAINER = 'TRAINER', 'Trainer'
    ADMIN = 'ADMIN', 'Admin'


class User(AbstractUser):
    """
    Custom user model inheriting all standard Django auth fields
    (username, email, password, is_staff, is_active, date_joined)
    plus our business-specific fields.
    """
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.CLIENT,
        help_text="Role of the user in the club ecosystem",
    )
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="Primary phone number for SMS and hold notifications",
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name or self.username} ({self.get_role_display()})"

    @property
    def is_client(self) -> bool:
        return self.role == UserRole.CLIENT

    @property
    def is_trainer(self) -> bool:
        return self.role == UserRole.TRAINER

    @property
    def is_gym_admin(self) -> bool:
        return self.role == UserRole.ADMIN or self.is_staff or self.is_superuser
