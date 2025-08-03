"""
Utility functions for the bug tracker application.
Contains reusable helper functions and business logic.
"""
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Project, Bug, Comment, ActivityLog
import logging

logger = logging.getLogger('tracker.utils')


def get_user_accessible_projects(user):
    """
    Get all projects that a user has access to.
    
    Args:
        user: Django User instance
        
    Returns:
        QuerySet: Projects the user can access
    """
    return Project.objects.filter(
        Q(project_owner=user) |
        Q(project_bugs__assigned_to_user=user) |
        Q(project_bugs__created_by_user=user)
    ).distinct()


def get_bug_notification_recipients(bug):
    """
    Get list of user IDs who should be notified about bug changes.
    
    Args:
        bug: Bug instance
        
    Returns:
        list: User IDs to notify
    """
    recipients = []
    
    # Add bug creator
    if bug.created_by_user:
        recipients.append(bug.created_by_user.id)
    
    # Add assigned user
    if bug.assigned_to_user:
        recipients.append(bug.assigned_to_user.id)
    
    # Add project owner
    recipients.append(bug.related_project.project_owner.id)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_recipients = []
    for user_id in recipients:
        if user_id not in seen:
            seen.add(user_id)
            unique_recipients.append(user_id)
    
    return unique_recipients


def create_activity_log(activity_type, description, project, user, bug=None):
    """
    Create an activity log entry with proper error handling.
    
    Args:
        activity_type: Type of activity from ActivityLog.ACTIVITY_TYPES
        description: Description of the activity
        project: Related project
        user: User who performed the activity
        bug: Related bug (optional)
        
    Returns:
        ActivityLog: Created activity log instance or None if failed
    """
    try:
        return ActivityLog.log_activity(
            activity_type=activity_type,
            description=description,
            project=project,
            user=user,
            bug=bug
        )
    except Exception as e:
        logger.error(f"Failed to create activity log: {str(e)}")
        return None 