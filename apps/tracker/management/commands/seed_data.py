"""
Management command to seed the database with test data.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.tracker.models import Project, Bug, Comment, ActivityLog
from apps.tracker.services import create_activity_log
import logging

logger = logging.getLogger('tracker.seed')


class Command(BaseCommand):
    help = 'Seed the database with test data'

    def handle(self, *args, **options):
        self.stdout.write('Starting to seed database...')
        
        try:
            # Create test users
            self.stdout.write('Creating test users...')
            
            # Get or create admin user
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@example.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                self.stdout.write(self.style.SUCCESS('Created admin user'))
            
            # Create test users
            test_users = [
                {
                    'username': 'developer1',
                    'email': 'dev1@example.com',
                    'first_name': 'John',
                    'last_name': 'Developer'
                },
                {
                    'username': 'developer2',
                    'email': 'dev2@example.com',
                    'first_name': 'Jane',
                    'last_name': 'Coder'
                },
                {
                    'username': 'tester1',
                    'email': 'tester1@example.com',
                    'first_name': 'Bob',
                    'last_name': 'Tester'
                }
            ]
            
            created_users = []
            for user_data in test_users:
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults=user_data
                )
                if created:
                    user.set_password('password123')
                    user.save()
                    created_users.append(user)
                    self.stdout.write(f'Created user: {user.username}')
            
            # Create test projects
            self.stdout.write('Creating test projects...')
            
            projects_data = [
                {
                    'project_name': 'E-commerce Platform',
                    'project_description': 'A modern e-commerce platform with payment integration',
                    'project_owner': admin_user
                },
                {
                    'project_name': 'Mobile App',
                    'project_description': 'Cross-platform mobile application for iOS and Android',
                    'project_owner': admin_user
                },
                {
                    'project_name': 'API Gateway',
                    'project_description': 'Microservices API gateway with authentication and rate limiting',
                    'project_owner': created_users[0] if created_users else admin_user
                }
            ]
            
            created_projects = []
            for project_data in projects_data:
                project, created = Project.objects.get_or_create(
                    project_name=project_data['project_name'],
                    defaults=project_data
                )
                if created:
                    created_projects.append(project)
                    self.stdout.write(f'Created project: {project.project_name}')
                    
                    # Create activity log for project creation
                    create_activity_log(
                        activity_type='project_created',
                        description=f"Project '{project.project_name}' was created",
                        project=project,
                        user=project.project_owner
                    )
            
            # Create test bugs
            self.stdout.write('Creating test bugs...')
            
            bugs_data = [
                {
                    'bug_title': 'Login page not responsive',
                    'bug_description': 'The login page breaks on mobile devices with screen width less than 768px',
                    'bug_status': 'open',
                    'bug_priority': 'high',
                    'related_project': created_projects[0],
                    'created_by_user': created_users[0] if created_users else admin_user,
                    'assigned_to_user': created_users[1] if len(created_users) > 1 else admin_user
                },
                {
                    'bug_title': 'Payment gateway timeout',
                    'bug_description': 'Users experiencing timeout errors when processing payments with PayPal',
                    'bug_status': 'in_progress',
                    'bug_priority': 'critical',
                    'related_project': created_projects[0],
                    'created_by_user': created_users[2] if len(created_users) > 2 else admin_user,
                    'assigned_to_user': created_users[0] if created_users else admin_user
                },
                {
                    'bug_title': 'App crashes on startup',
                    'bug_description': 'Application crashes immediately after launch on Android 12 devices',
                    'bug_status': 'resolved',
                    'bug_priority': 'high',
                    'related_project': created_projects[1],
                    'created_by_user': created_users[1] if len(created_users) > 1 else admin_user,
                    'assigned_to_user': created_users[0] if created_users else admin_user
                },
                {
                    'bug_title': 'API rate limiting not working',
                    'bug_description': 'Rate limiting middleware is not properly limiting requests per IP',
                    'bug_status': 'open',
                    'bug_priority': 'medium',
                    'related_project': created_projects[2],
                    'created_by_user': admin_user,
                    'assigned_to_user': created_users[1] if len(created_users) > 1 else admin_user
                }
            ]
            
            created_bugs = []
            for bug_data in bugs_data:
                bug, created = Bug.objects.get_or_create(
                    bug_title=bug_data['bug_title'],
                    related_project=bug_data['related_project'],
                    defaults=bug_data
                )
                if created:
                    created_bugs.append(bug)
                    self.stdout.write(f'Created bug: {bug.bug_title}')
                    
                    # Create activity log for bug creation
                    create_activity_log(
                        activity_type='bug_created',
                        description=f"Bug '{bug.bug_title}' was created",
                        project=bug.related_project,
                        user=bug.created_by_user,
                        bug=bug
                    )
            
            # Create test comments
            self.stdout.write('Creating test comments...')
            
            comments_data = [
                {
                    'comment_message': 'I can reproduce this issue on my iPhone 13. The app crashes immediately after the splash screen.',
                    'related_bug': created_bugs[2],
                    'commenter_user': created_users[1] if len(created_users) > 1 else admin_user
                },
                {
                    'comment_message': 'This is a critical issue affecting our production environment. Please prioritize this fix.',
                    'related_bug': created_bugs[1],
                    'commenter_user': admin_user
                },
                {
                    'comment_message': 'I\'ve started investigating the rate limiting issue. It seems to be related to the Redis configuration.',
                    'related_bug': created_bugs[3],
                    'commenter_user': created_users[1] if len(created_users) > 1 else admin_user
                },
                {
                    'comment_message': 'The login page works fine on my end. Can you provide more details about the specific device and browser?',
                    'related_bug': created_bugs[0],
                    'commenter_user': created_users[0] if created_users else admin_user
                }
            ]
            
            for comment_data in comments_data:
                comment, created = Comment.objects.get_or_create(
                    comment_message=comment_data['comment_message'],
                    related_bug=comment_data['related_bug'],
                    commenter_user=comment_data['commenter_user'],
                    defaults=comment_data
                )
                if created:
                    self.stdout.write(f'Created comment on bug: {comment.related_bug.bug_title}')
                    
                    # Create activity log for comment
                    create_activity_log(
                        activity_type='comment_added',
                        description=f"Comment added to bug '{comment.related_bug.bug_title}'",
                        project=comment.related_bug.related_project,
                        user=comment.commenter_user,
                        bug=comment.related_bug
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully seeded database with:\n'
                    f'- {User.objects.count()} users\n'
                    f'- {Project.objects.count()} projects\n'
                    f'- {Bug.objects.count()} bugs\n'
                    f'- {Comment.objects.count()} comments\n'
                    f'- {ActivityLog.objects.count()} activity logs'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error seeding database: {str(e)}')
            )
            logger.error(f'Error seeding database: {str(e)}') 