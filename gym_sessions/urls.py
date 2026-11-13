from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrainerReadOnlyViewSet, GymSessionReadOnlyViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'trainers', TrainerReadOnlyViewSet, basename='trainer')
router.register(r'sessions', GymSessionReadOnlyViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
]
