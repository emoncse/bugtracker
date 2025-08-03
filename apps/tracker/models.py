from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import logging

# Set up logging for models
logger = logging.getLogger('tracker.models')


class Project(models.Model):
    """
    Represents a project in the bug tracking system.
    Each project has an owner and can contain multiple bugs.
    """
    project_name = models.CharField(max_length=200, help_text="Name of the project")
    project_description = models.TextField(help_text="Detailed description of the project")
    project_owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='owned_projects',
        help_text="User who owns this project"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"{self.project_name} (Owner: {self.project_owner.username})"

    def save(self, *args, **kwargs):
        """Override save method to log project changes"""
        is_new_project = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new_project:
            logger.info(f"New project created: {self.project_name} by {self.project_owner.username}")
        else:
            logger.info(f"Project updated: {self.project_name} by {self.project_owner.username}")

    @property
    def total_bugs_count(self):
        """Get total number of bugs in this project"""
        return self.project_bugs.count()

    @property
    def open_bugs_count(self):
        """Get number of open bugs in this project"""
        return self.project_bugs.filter(bug_status='open').count()

    # TODO: Add project archiving functionality
    # TODO: Implement project member roles and permissions
    # TODO: Add project templates for quick setup


class Bug(models.Model):
    """
    Represents a bug in the tracking system.
    Each bug belongs to a project and can be assigned to a user.
    """
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    bug_title = models.CharField(max_length=200, help_text="Title of the bug")
    bug_description = models.TextField(help_text="Detailed description of the bug")
    bug_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='open',
        help_text="Current status of the bug"
    )
    bug_priority = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        help_text="Priority level of the bug"
    )
    assigned_to_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_bugs',
        help_text="User assigned to fix this bug"
    )
    related_project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='project_bugs',
        help_text="Project this bug belongs to"
    )
    created_by_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_bugs',
        help_text="User who reported this bug"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bug"
        verbose_name_plural = "Bugs"

    def __str__(self):
        return f"{self.bug_title} [{self.bug_status}] ({self.related_project.project_name})"

    def save(self, *args, **kwargs):
        """Override save method to log bug changes and status updates"""
        is_new_bug = self.pk is None
        old_status = None
        
        if not is_new_bug:
            # Get the old status before saving for comparison
            try:
                existing_bug = Bug.objects.get(pk=self.pk)
                old_status = existing_bug.bug_status
            except Bug.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        if is_new_bug:
            logger.info(f"New bug created: {self.bug_title} in project {self.related_project.project_name}")
        else:
            if old_status and old_status != self.bug_status:
                logger.info(f"Bug status changed: {self.bug_title} from {old_status} to {self.bug_status}")
            else:
                logger.info(f"Bug updated: {self.bug_title}")

    @property
    def comments_count(self):
        """Get total number of comments on this bug"""
        return self.bug_comments.count()

    def is_assigned_to_user(self, user):
        """Check if bug is assigned to the given user"""
        return self.assigned_to_user == user

    def can_user_edit(self, user):
        """Check if user has permission to edit this bug"""
        return (user == self.created_by_user or 
                user == self.assigned_to_user or 
                user == self.related_project.project_owner)

    # TODO: Add bug duplication detection
    # TODO: Implement bug templates for common issues
    # TODO: Add bug time tracking functionality


class Comment(models.Model):
    """
    Represents a comment on a bug.
    Each comment belongs to a specific bug and is created by a user.
    """
    related_bug = models.ForeignKey(
        Bug, 
        on_delete=models.CASCADE, 
        related_name='bug_comments',
        help_text="Bug this comment belongs to"
    )
    commenter_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_comments',
        help_text="User who made this comment"
    )
    comment_message = models.TextField(help_text="Content of the comment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return f"Comment by {self.commenter_user.username} on {self.related_bug.bug_title}"

    def save(self, *args, **kwargs):
        """Override save method to log comment changes"""
        is_new_comment = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new_comment:
            logger.info(f"New comment added by {self.commenter_user.username} on bug: {self.related_bug.bug_title}")
        else:
            logger.info(f"Comment updated by {self.commenter_user.username} on bug: {self.related_bug.bug_title}")

    def can_user_edit(self, user):
        """Check if user has permission to edit this comment"""
        return self.commenter_user == user

    # TODO: Add comment moderation features
    # TODO: Implement comment threading/replies
    # TODO: Add comment editing history tracking


class ActivityLog(models.Model):
    """
    Tracks all activities in the bug tracker system.
    Used for real-time activity streaming via WebSocket.
    """
    
    ACTIVITY_TYPES = [
        ('bug_created', 'Bug Created'),
        ('bug_updated', 'Bug Updated'),
        ('bug_status_changed', 'Bug Status Changed'),
        ('comment_added', 'Comment Added'),
        ('project_created', 'Project Created'),
        ('project_updated', 'Project Updated'),
    ]
    
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    activity_description = models.TextField(help_text="Description of the activity")
    related_project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='project_activities',
        help_text="Project related to this activity"
    )
    activity_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_activities',
        help_text="User who performed this activity"
    )
    related_bug = models.ForeignKey(
        Bug, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='bug_activities',
        help_text="Bug related to this activity (if applicable)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"

    def __str__(self):
        return f"{self.activity_type}: {self.activity_description} by {self.activity_user.username}"

    def save(self, *args, **kwargs):
        """Override save method to log activity creation"""
        super().save(*args, **kwargs)
        logger.info(f"Activity logged: {self.activity_type} - {self.activity_description}")

    @classmethod
    def log_activity(cls, activity_type, description, project, user, bug=None):
        """
        Convenience method to create activity logs.
        
        Args:
            activity_type: Type of activity from ACTIVITY_TYPES
            description: Description of the activity
            project: Related project
            user: User who performed the activity
            bug: Related bug (optional)
        """
        return cls.objects.create(
            activity_type=activity_type,
            activity_description=description,
            related_project=project,
            activity_user=user,
            related_bug=bug
        )

    # TODO: Add activity log cleanup for old entries
    # TODO: Implement activity log export functionality
    # TODO: Add activity log analytics and reporting

