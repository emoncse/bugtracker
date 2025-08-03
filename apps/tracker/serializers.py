"""
Serializers module for the tracker application.
This module provides backward compatibility by importing from versioned serializers.
"""

# Import all serializers from versioned structure for backward compatibility
from .serializers.serializers_v1 import (
    UserSerializer,
    ProjectSerializer,
    BugSerializer,
    CommentSerializer,
    ActivityLogSerializer,
    BugFilterSerializer
)

__all__ = [
    'UserSerializer',
    'ProjectSerializer',
    'BugSerializer',
    'CommentSerializer',
    'ActivityLogSerializer',
    'BugFilterSerializer'
]

