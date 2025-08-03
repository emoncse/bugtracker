"""
Views module for the tracker application.
This module provides backward compatibility by importing from versioned views.
"""

# Import all views from versioned structure for backward compatibility
from .views.views_v1 import (
    landing_page,
    ProjectViewSet,
    BugViewSet,
    CommentViewSet,
    ActivityLogViewSet
)

__all__ = [
    'landing_page',
    'ProjectViewSet',
    'BugViewSet',
    'CommentViewSet',
    'ActivityLogViewSet'
]

