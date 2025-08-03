"""
Version 1 views for the tracker application.
Contains all viewsets for the API v1 endpoints.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from ...models import Project, Bug, Comment, ActivityLog
from .serializers import (
    ProjectSerializer, BugSerializer, CommentSerializer, 
    ActivityLogSerializer, UserSerializer, BugFilterSerializer
)
from ...websocket_utils import send_websocket_notification
from ...services import get_user_accessible_projects, get_bug_notification_recipients, create_activity_log
import logging

# Set up logging for API views
logger = logging.getLogger('tracker.api')


def landing_page(request):
    """
    Simple landing page with links to API documentation.
    """
    return render(request, 'tracker/landing.html')


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing projects with full CRUD operations.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['project_name', 'project_description']
    ordering_fields = ['created_at', 'updated_at', 'project_name']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter projects based on user permissions.
        Users can see projects they own or are involved in.
        """
        current_user = self.request.user
        
        # Get projects user has access to
        accessible_projects = get_user_accessible_projects(current_user)
        
        logger.info(f"User {current_user.username} requested projects list")
        return accessible_projects

    def perform_create(self, serializer):
        """Set the current user as project owner when creating"""
        new_project = serializer.save(project_owner=self.request.user)
        logger.info(f"Project created: {new_project.project_name} by {self.request.user.username}")
        
        # Create activity log
        create_activity_log(
            activity_type='project_created',
            description=f"Project '{new_project.project_name}' was created",
            project=new_project,
            user=self.request.user
        )

    def perform_update(self, serializer):
        """Log project updates"""
        updated_project = serializer.save()
        logger.info(f"Project updated: {updated_project.project_name} by {self.request.user.username}")
        
        # Create activity log
        create_activity_log(
            activity_type='project_updated',
            description=f"Project '{updated_project.project_name}' was updated",
            project=updated_project,
            user=self.request.user
        )

    @action(detail=True, methods=['get'])
    def project_bugs(self, request, pk=None):
        """
        Get all bugs for a specific project.
        """
        try:
            project_instance = self.get_object()
            project_bugs = project_instance.project_bugs.select_related(
                'assigned_to_user', 'created_by_user'
            ).prefetch_related('bug_comments')
            
            serializer = BugSerializer(project_bugs, many=True, context={'request': request})
            logger.info(f"Retrieved {len(project_bugs)} bugs for project {project_instance.project_name}")
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error retrieving bugs for project {pk}: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve project bugs'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # TODO: Add project statistics endpoint with bug counts by status
    # TODO: Add project member management functionality
    # TODO: Implement project archiving feature


class BugViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bugs with full CRUD operations and filtering.
    """
    queryset = Bug.objects.all()
    serializer_class = BugSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['bug_status', 'bug_priority', 'related_project', 'assigned_to_user']
    search_fields = ['bug_title', 'bug_description']
    ordering_fields = ['created_at', 'updated_at', 'bug_priority']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter bugs based on query parameters and user permissions.
        """
        queryset = Bug.objects.select_related(
            'assigned_to_user', 'created_by_user', 'related_project'
        ).prefetch_related('bug_comments')
        current_user = self.request.user
        
        # Apply filters based on query parameters
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(bug_status=status_filter)
            logger.info(f"Filtering bugs by status: {status_filter}")
        
        project_filter = self.request.query_params.get('project', None)
        if project_filter:
            queryset = queryset.filter(related_project_id=project_filter)
            logger.info(f"Filtering bugs by project ID: {project_filter}")
        
        assigned_user_filter = self.request.query_params.get('assigned_to', None)
        if assigned_user_filter:
            queryset = queryset.filter(assigned_to_user_id=assigned_user_filter)
            logger.info(f"Filtering bugs by assigned user ID: {assigned_user_filter}")
        
        logger.info(f"User {current_user.username} requested bugs list with {queryset.count()} results")
        return queryset

    def perform_create(self, serializer):
        """Create bug with proper logging and WebSocket notification"""
        new_bug = serializer.save(created_by_user=self.request.user)
        logger.info(f"Bug created: {new_bug.bug_title} by {self.request.user.username}")
        
        # Create activity log
        create_activity_log(
            activity_type='bug_created',
            description=f"Bug '{new_bug.bug_title}' was created",
            project=new_bug.related_project,
            user=self.request.user,
            bug=new_bug
        )
        
        # Send WebSocket notification to project team
        send_websocket_notification(
            project_id=new_bug.related_project.id,
            notification_type='bug_created',
            notification_data={
                'bug_id': new_bug.id,
                'bug_title': new_bug.bug_title,
                'created_by': self.request.user.username,
                'project_name': new_bug.related_project.project_name
            }
        )

    def perform_update(self, serializer):
        """Update bug with proper logging and WebSocket notification"""
        # Get old bug data for comparison
        existing_bug = get_object_or_404(Bug, pk=serializer.instance.pk)
        old_status = existing_bug.bug_status
        
        updated_bug = serializer.save()
        logger.info(f"Bug updated: {updated_bug.bug_title} by {self.request.user.username}")
        
        # Check if status changed and handle accordingly
        if old_status != updated_bug.bug_status:
            logger.info(f"Bug status changed: {updated_bug.bug_title} from {old_status} to {updated_bug.bug_status}")
            
            # Create activity log for status change
            create_activity_log(
                activity_type='bug_status_changed',
                description=f"Bug '{updated_bug.bug_title}' status changed from {old_status} to {updated_bug.bug_status}",
                project=updated_bug.related_project,
                user=self.request.user,
                bug=updated_bug
            )
            
            # Send WebSocket notification for status change
            send_websocket_notification(
                project_id=updated_bug.related_project.id,
                notification_type='bug_status_changed',
                notification_data={
                    'bug_id': updated_bug.id,
                    'bug_title': updated_bug.bug_title,
                    'old_status': old_status,
                    'new_status': updated_bug.bug_status,
                    'updated_by': self.request.user.username,
                    'project_name': updated_bug.related_project.project_name
                }
            )
        else:
            # Create activity log for general update
            create_activity_log(
                activity_type='bug_updated',
                description=f"Bug '{updated_bug.bug_title}' was updated",
                project=updated_bug.related_project,
                user=self.request.user,
                bug=updated_bug
            )
            
            # Send WebSocket notification for general update
            send_websocket_notification(
                project_id=updated_bug.related_project.id,
                notification_type='bug_updated',
                notification_data={
                    'bug_id': updated_bug.id,
                    'bug_title': updated_bug.bug_title,
                    'updated_by': self.request.user.username,
                    'project_name': updated_bug.related_project.project_name
                }
            )

    @action(detail=False, methods=['get'])
    def assigned_to_me(self, request):
        """
        Get all bugs assigned to the current user.
        """
        try:
            current_user = request.user
            assigned_bugs = Bug.objects.filter(assigned_to_user=current_user).select_related(
                'assigned_to_user', 'created_by_user', 'related_project'
            )
            
            serializer = BugSerializer(assigned_bugs, many=True, context={'request': request})
            logger.info(f"Retrieved {len(assigned_bugs)} bugs assigned to user {current_user.username}")
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error retrieving bugs assigned to user {request.user.username}: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve assigned bugs'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def created_by_me(self, request):
        """
        Get all bugs created by the current user.
        """
        try:
            current_user = request.user
            created_bugs = Bug.objects.filter(created_by_user=current_user).select_related(
                'assigned_to_user', 'created_by_user', 'related_project'
            )
            
            serializer = BugSerializer(created_bugs, many=True, context={'request': request})
            logger.info(f"Retrieved {len(created_bugs)} bugs created by user {current_user.username}")
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error retrieving bugs created by user {request.user.username}: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve created bugs'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # TODO: Add bulk update functionality for bug status
    # TODO: Implement bug assignment notifications
    # TODO: Add bug priority change tracking


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing comments with full CRUD operations.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['related_bug']
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_queryset(self):
        """
        Filter comments based on query parameters.
        """
        queryset = Comment.objects.select_related(
            'commenter_user', 'related_bug', 'related_bug__related_project'
        )
        current_user = self.request.user
        
        # Filter by bug if provided
        bug_filter = self.request.query_params.get('bug', None)
        if bug_filter:
            queryset = queryset.filter(related_bug_id=bug_filter)
            logger.info(f"Filtering comments by bug ID: {bug_filter}")
        
        logger.info(f"User {current_user.username} requested comments list with {queryset.count()} results")
        return queryset

    def perform_create(self, serializer):
        """Create comment with proper logging and WebSocket notification"""
        new_comment = serializer.save(commenter_user=self.request.user)
        logger.info(f"Comment created by {self.request.user.username} on bug {new_comment.related_bug.bug_title}")
        
        # Create activity log
        create_activity_log(
            activity_type='comment_added',
            description=f"Comment added to bug '{new_comment.related_bug.bug_title}'",
            project=new_comment.related_bug.related_project,
            user=self.request.user,
            bug=new_comment.related_bug
        )
        
        # Determine notification recipients
        notification_recipients = get_bug_notification_recipients(new_comment.related_bug)
        
        # Send WebSocket notification to bug creator and assigned user
        send_websocket_notification(
            project_id=new_comment.related_bug.related_project.id,
            notification_type='comment_added',
            notification_data={
                'comment_id': new_comment.id,
                'bug_id': new_comment.related_bug.id,
                'bug_title': new_comment.related_bug.bug_title,
                'comment_message': new_comment.comment_message,
                'commenter': self.request.user.username,
                'project_name': new_comment.related_bug.related_project.project_name,
                'recipients': notification_recipients
            }
        )

    # TODO: Add comment editing history tracking
    # TODO: Implement comment moderation features
    # TODO: Add comment threading support


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reading activity logs.
    """
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['activity_type', 'related_project', 'related_bug']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter activity logs based on user permissions and query parameters.
        """
        current_user = self.request.user
        
        # Get activities for projects user has access to
        accessible_activities = ActivityLog.objects.filter(
            Q(related_project__project_owner=current_user) |
            Q(related_project__project_bugs__assigned_to_user=current_user) |
            Q(related_project__project_bugs__created_by_user=current_user)
        ).distinct().select_related(
            'activity_user', 'related_project', 'related_bug'
        )
        
        # Filter by project if provided
        project_filter = self.request.query_params.get('project', None)
        if project_filter:
            accessible_activities = accessible_activities.filter(related_project_id=project_filter)
            logger.info(f"Filtering activities by project ID: {project_filter}")
        
        logger.info(f"User {current_user.username} requested activity logs with {accessible_activities.count()} results")
        return accessible_activities

    # TODO: Add activity export functionality
    # TODO: Implement activity filtering by date range
    # TODO: Add activity summary endpoints 