from django.db.models import Count, Q, F
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from datetime import timedelta
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from bookings.models import Booking, BookingStatus
from bookings.serializers import BookingHoldResponseSerializer
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
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session_type', 'status', 'trainer']
    ordering_fields = ['starts_at', 'price']
    ordering = ['starts_at']

    def get_permissions(self):
        # Anyone can view the schedule; only logged-in users can place a hold
        if self.action == 'hold':
            return [IsAuthenticated()]
        return [AllowAny()]    

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

    @action(detail=True, methods=['post'], url_path='hold')
    def hold(self, request, pk=None):
        """
        POST /api/v1/sessions/{id}/hold/
        Places a 10-minute temporary lock on a seat with pessimistic row-level locking.
        """
        now = timezone.now()

        # Wrap in a database transaction with a row lock
        with transaction.atomic():
            # 1. Lock the GymSession row exclusively
            try:
                session = GymSession.objects.select_for_update().get(pk=pk)
            except GymSession.DoesNotExist:
                return Response(
                    {"detail": "Session not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 2. Check session validity (must be SCHEDULED and in the future)
            if session.status != GymSession.SessionStatus.SCHEDULED:
                return Response(
                    {"detail": "This session is not available for booking."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if session.starts_at <= now:
                return Response(
                    {"detail": "Cannot book a session that has already started or passed."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 3. Check if the user already has an active booking (HELD or CONFIRMED)
            existing_booking = Booking.objects.filter(
                user=request.user,
                session=session,
                status__in=[BookingStatus.HELD, BookingStatus.CONFIRMED]
            ).filter(
                # If HELD, check that it hasn't expired yet
                Q(status=BookingStatus.CONFIRMED) | Q(status=BookingStatus.HELD, expires_at__gt=now)
            ).exists()

            if existing_booking:
                return Response(
                    {"detail": "You already have an active hold or confirmed booking for this session."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 4. Count currently occupied spots under the lock
            active_count = Booking.objects.filter(
                session=session
            ).filter(
                Q(status=BookingStatus.CONFIRMED) | Q(status=BookingStatus.HELD, expires_at__gt=now)
            ).count()

            # 5. Check capacity
            if active_count >= session.max_capacity:
                return Response(
                    {"detail": "This session is fully booked. Please join the waitlist."},
                    status=status.HTTP_409_CONFLICT
                )

            # 6. Create the 10-minute hold
            expires_at = now + timedelta(minutes=10)
            booking = Booking.objects.create(
                user=request.user,
                session=session,
                status=BookingStatus.HELD,
                expires_at=expires_at,
            )

            serializer = BookingHoldResponseSerializer(booking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)        

    def get_serializer_class(self):
        # Return lightweight list serializer for schedule, detail serializer for single session
        if self.action == 'retrieve':
            return GymSessionDetailSerializer
        return GymSessionListSerializer
