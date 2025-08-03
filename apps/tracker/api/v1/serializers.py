"""
Version 1 serializers for the tracker application.
Contains all serializers for the API v1 endpoints.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from ...models import Project, Bug, Comment, ActivityLog
import logging

# Set up logging for serializers
logger = logging.getLogger('tracker.api')


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model to include user information in responses.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Project model with detailed information.
    """
    project_owner = UserSerializer(read_only=True)
    project_owner_id = serializers.IntegerField(write_only=True, required=False)
    total_bugs_count = serializers.SerializerMethodField()
    open_bugs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'project_name', 'project_description', 'project_owner', 
            'project_owner_id', 'total_bugs_count', 'open_bugs_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_bugs_count(self, project_instance):
        """Get total number of bugs in this project"""
        return project_instance.total_bugs_count

    def get_open_bugs_count(self, project_instance):
        """Get number of open bugs in this project"""
        return project_instance.open_bugs_count

    def create(self, validated_data):
        """Create a new project with proper logging"""
        project_owner_id = validated_data.pop('project_owner_id', None)
        if project_owner_id:
            validated_data['project_owner_id'] = project_owner_id
        else:
            # Set the current user as owner if not specified
            validated_data['project_owner'] = self.context['request'].user
        
        new_project = Project.objects.create(**validated_data)
        logger.info(f"Project created via API: {new_project.project_name} by {new_project.project_owner.username}")
        return new_project


class BugSerializer(serializers.ModelSerializer):
    """
    Serializer for Bug model with comprehensive information.
    """
    assigned_to_user = UserSerializer(read_only=True)
    assigned_to_user_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    related_project = ProjectSerializer(read_only=True)
    related_project_id = serializers.IntegerField(write_only=True)
    created_by_user = UserSerializer(read_only=True)
    created_by_user_id = serializers.IntegerField(write_only=True, required=False)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Bug
        fields = [
            'id', 'bug_title', 'bug_description', 'bug_status', 'bug_priority',
            'assigned_to_user', 'assigned_to_user_id', 'related_project', 'related_project_id',
            'created_by_user', 'created_by_user_id', 'comments_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_comments_count(self, bug_instance):
        """Get total number of comments on this bug"""
        return bug_instance.comments_count

    def create(self, validated_data):
        """Create a new bug with proper logging"""
        created_by_user_id = validated_data.pop('created_by_user_id', None)
        if created_by_user_id:
            validated_data['created_by_user_id'] = created_by_user_id
        else:
            # Set the current user as creator if not specified
            validated_data['created_by_user'] = self.context['request'].user
        
        new_bug = Bug.objects.create(**validated_data)
        logger.info(f"Bug created via API: {new_bug.bug_title} by {new_bug.created_by_user.username}")
        return new_bug

    def update(self, bug_instance, validated_data):
        """Update bug with proper logging"""
        old_status = bug_instance.bug_status
        updated_bug = super().update(bug_instance, validated_data)
        
        if old_status != updated_bug.bug_status:
            logger.info(f"Bug status updated via API: {updated_bug.bug_title} from {old_status} to {updated_bug.bug_status}")
        else:
            logger.info(f"Bug updated via API: {updated_bug.bug_title}")
        
        return updated_bug


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model with user and bug information.
    """
    commenter_user = UserSerializer(read_only=True)
    commenter_user_id = serializers.IntegerField(write_only=True, required=False)
    related_bug = BugSerializer(read_only=True)
    related_bug_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'comment_message', 'commenter_user', 'commenter_user_id',
            'related_bug', 'related_bug_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create a new comment with proper logging"""
        commenter_user_id = validated_data.pop('commenter_user_id', None)
        if commenter_user_id:
            validated_data['commenter_user_id'] = commenter_user_id
        else:
            # Set the current user as commenter if not specified
            validated_data['commenter_user'] = self.context['request'].user
        
        new_comment = Comment.objects.create(**validated_data)
        logger.info(f"Comment created via API by {new_comment.commenter_user.username} on bug {new_comment.related_bug.bug_title}")
        return new_comment


class ActivityLogSerializer(serializers.ModelSerializer):
    """
    Serializer for ActivityLog model for streaming activities.
    """
    activity_user = UserSerializer(read_only=True)
    related_project = ProjectSerializer(read_only=True)
    related_bug = BugSerializer(read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'activity_type', 'activity_description', 'activity_user',
            'related_project', 'related_bug', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BugFilterSerializer(serializers.Serializer):
    """
    Serializer for filtering bugs by various criteria.
    """
    bug_status = serializers.ChoiceField(
        choices=Bug.STATUS_CHOICES, 
        required=False,
        help_text="Filter bugs by status"
    )
    related_project_id = serializers.IntegerField(
        required=False,
        help_text="Filter bugs by project ID"
    )
    assigned_to_user_id = serializers.IntegerField(
        required=False,
        help_text="Filter bugs assigned to specific user"
    )
    bug_priority = serializers.ChoiceField(
        choices=Bug.PRIORITY_CHOICES,
        required=False,
        help_text="Filter bugs by priority"
    ) 