from rest_framework import serializers
from .models import Trainer, GymSession

class TrainerSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Trainer
        fields = [
            'id',
            'username',
            'full_name',
            'specialty',
            'bio',
            'is_active',
            'created_at',
        ]

class TrainerDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Trainer
        fields = [
            'id',
            'username',
            'full_name',
            'specialty',
            'bio',
            'is_active',
            'created_at',
        ]


class GymSessionListSerializer(serializers.ModelSerializer):
    trainer = TrainerSummarySerializer(read_only=True)
    session_type_display = serializers.CharField(source='get_session_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    available_capacity = serializers.IntegerField(read_only=True)


    class Meta:
        model = GymSession
        fields = [
            'id',
            'title',
            'trainer',
            'session_type',
            'session_type_display',
            'starts_at',
            'ends_at',
            'price',
            'max_capacity',
            'available_capacity',
            'status',
            'status_display',
            'is_private',
        ]    



class GymSessionDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for single session view (full description + trainer bio).
    """
    trainer = TrainerDetailSerializer(read_only=True)
    session_type_display = serializers.CharField(source='get_session_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    available_capacity = serializers.IntegerField(read_only=True)
    class Meta:
        model = GymSession
        fields = [
            'id',
            'title',
            'description',
            'trainer',
            'session_type',
            'session_type_display',
            'starts_at',
            'ends_at',
            'price',
            'max_capacity',
            'available_capacity',
            'status',
            'status_display',
            'is_private',
            'created_at',
        ]