"""
Services module for the tracker application.
Contains business logic and data abstractions.
"""

from django.contrib.auth.models import User
from django.db.models import Q
from .models import Project, Bug, Comment, ActivityLog
import logging

logger = logging.getLogger('tracker.services')


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


def get_user_bugs(user, filters=None):
    """
    Get bugs for a user with optional filtering.
    
    Args:
        user: Django User instance
        filters: Optional dict of filters to apply
        
    Returns:
        QuerySet: Filtered bugs for the user
    """
    queryset = Bug.objects.select_related(
        'assigned_to_user', 'created_by_user', 'related_project'
    ).prefetch_related('bug_comments')
    
    if filters:
        if filters.get('status'):
            queryset = queryset.filter(bug_status=filters['status'])
        if filters.get('project_id'):
            queryset = queryset.filter(related_project_id=filters['project_id'])
        if filters.get('assigned_to'):
            queryset = queryset.filter(assigned_to_user_id=filters['assigned_to'])
    
    return queryset


def can_user_access_project(user, project_id):
    """
    Check if a user has access to a specific project.
    
    Args:
        user: Django User instance
        project_id: ID of the project to check
        
    Returns:
        bool: True if user has access, False otherwise
    """
    try:
        project = Project.objects.get(id=project_id)
        return (project.project_owner == user or
                project.project_bugs.filter(assigned_to_user=user).exists() or
                project.project_bugs.filter(created_by_user=user).exists())
    except Project.DoesNotExist:
        return False


def validate_bug_status_transition(old_status, new_status):
    """
    Validate if a bug status transition is allowed.
    
    Args:
        old_status: Current bug status
        new_status: New bug status
        
    Returns:
        bool: True if transition is valid, False otherwise
    """
    valid_transitions = {
        'open': ['in_progress', 'resolved'],
        'in_progress': ['open', 'resolved'],
        'resolved': ['open', 'in_progress']
    }
    
    return new_status in valid_transitions.get(old_status, [])


def get_project_statistics(project):
    """
    Get statistics for a project.
    
    Args:
        project: Project instance
        
    Returns:
        dict: Project statistics
    """
    bugs = project.project_bugs.all()
    
    return {
        'total_bugs': bugs.count(),
        'open_bugs': bugs.filter(bug_status='open').count(),
        'in_progress_bugs': bugs.filter(bug_status='in_progress').count(),
        'resolved_bugs': bugs.filter(bug_status='resolved').count(),
        'high_priority_bugs': bugs.filter(bug_priority__in=['high', 'critical']).count(),
    }


def format_error_message(error, context=None):
    """
    Format error messages for API responses.
    
    Args:
        error: Exception or error message
        context: Additional context information
        
    Returns:
        str: Formatted error message
    """
    if isinstance(error, Exception):
        error_msg = str(error)
    else:
        error_msg = error
    
    if context:
        return f"{error_msg} (Context: {context})"
    
    return error_msg 