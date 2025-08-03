from django.contrib import admin
from .models import Project, Bug, Comment, ActivityLog


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['project_name', 'project_owner', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'project_owner']
    search_fields = ['project_name', 'project_description', 'project_owner__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Bug)
class BugAdmin(admin.ModelAdmin):
    list_display = ['bug_title', 'bug_status', 'bug_priority', 'assigned_to_user', 'related_project', 'created_by_user', 'created_at']
    list_filter = ['bug_status', 'bug_priority', 'created_at', 'updated_at', 'related_project']
    search_fields = ['bug_title', 'bug_description', 'assigned_to_user__username', 'created_by_user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Bug Information', {
            'fields': ('bug_title', 'bug_description', 'bug_status', 'bug_priority')
        }),
        ('Assignment', {
            'fields': ('related_project', 'assigned_to_user', 'created_by_user')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['related_bug', 'commenter_user', 'comment_message_preview', 'created_at']
    list_filter = ['created_at', 'updated_at', 'commenter_user']
    search_fields = ['comment_message', 'commenter_user__username', 'related_bug__bug_title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def comment_message_preview(self, obj):
        """Show preview of comment message in admin list"""
        return obj.comment_message[:50] + "..." if len(obj.comment_message) > 50 else obj.comment_message
    comment_message_preview.short_description = 'Comment Preview'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['activity_type', 'activity_user', 'related_project', 'related_bug', 'created_at']
    list_filter = ['activity_type', 'created_at', 'related_project']
    search_fields = ['activity_description', 'activity_user__username', 'related_project__project_name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('activity_type', 'activity_description', 'activity_user')
        }),
        ('Related Objects', {
            'fields': ('related_project', 'related_bug')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

