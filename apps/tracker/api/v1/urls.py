"""
Version 1 URL patterns for the tracker application.
Contains all URL patterns for the API v1 endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    ProjectViewSet, BugViewSet, CommentViewSet, ActivityLogViewSet
)

# Create router for ViewSets
api_router = DefaultRouter()
api_router.register(r'projects', ProjectViewSet)
api_router.register(r'bugs', BugViewSet)
api_router.register(r'comments', CommentViewSet)
api_router.register(r'activities', ActivityLogViewSet)

urlpatterns = [
    # JWT Authentication endpoints
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API endpoints
    path('api/', include(api_router.urls)),
] 