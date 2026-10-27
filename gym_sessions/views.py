from django.db.models import Count, Q, F
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny

from bookings.models import BookingStatus
from .models import Trainer, GymSession
from .serializers import (
    TrainerSummarySerializer,
    TrainerDetailSerializer,
    GymSessionListSerializer,
    GymSessionDetailSerializer,
)


class TrainerReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public catalog for trainers.
    Provides:
      - GET /api/v1/trainers/
      - GET /api/v1/trainers/{id}/
    """
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'specialty']
    ordering_fields = ['user__first_name', 'created_at']

    def get_queryset(self):
        # select_related('user') prevents N+1 query when reading coach names
        return Trainer.objects.filter(is_active=True).select_related('user')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TrainerDetailSerializer
        return TrainerSummarySerializer


class GymSessionReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public catalog for gym sessions with zero N+1 queries.
    Provides:
      - GET /api/v1/sessions/
      - GET /api/v1/sessions/{id}/
    """
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session_type', 'status', 'trainer']
    ordering_fields = ['starts_at', 'price']
    ordering = ['starts_at']

    def get_queryset(self):
        now = timezone.now()

        # Filter criteria for an occupied seat:
        # A seat is taken if it's CONFIRMED or currently HELD (not expired).
        active_bookings_filter = (
            Q(bookings__status=BookingStatus.CONFIRMED) |
            Q(bookings__status=BookingStatus.HELD, bookings__expires_at__gt=now)
        )

        return (
            GymSession.objects
            .select_related('trainer__user')  # Single JOIN for session + trainer + user
            .annotate(
                active_bookings_count=Count(
                    'bookings',
                    filter=active_bookings_filter,
                    distinct=True
                )
            )
            .annotate(
                # Available capacity = max_capacity - active_bookings_count
                available_capacity=F('max_capacity') - F('active_bookings_count')
            )
        )

    def get_serializer_class(self):
        # Return lightweight list serializer for schedule, detail serializer for single session
        if self.action == 'retrieve':
            return GymSessionDetailSerializer
        return GymSessionListSerializer
