from rest_framework import serializers
from .models import Booking

class BookingHoldResponseSerializer(serializers.ModelSerializer):
    """
    Serializer returned when a user successfully creates a 10-minute hold.
    Provides the booking ID and exact expiration time for the mobile countdown.
    """
    session_id = serializers.IntegerField(source='session.id', read_only=True)
    session_title = serializers.CharField(source='session.title', read_only=True)
    session_type = serializers.CharField(source='session.session_type', read_only=True)
    price = serializers.DecimalField(source='session.price', max_digits=10, decimal_places=2, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)


    class Meta:
        model = Booking
        fields = [
            'id',
            'session_id',
            'session_title',
            'session_type',
            'price',
            'status',
            'status_display',
            'created_at',
            'expires_at',
        ]