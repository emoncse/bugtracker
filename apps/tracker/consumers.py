import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Project, ActivityLog
from .websocket_utils import get_project_room_name, validate_websocket_message
import logging

# Set up logging for WebSocket consumers
logger = logging.getLogger('tracker.websocket')


class TrackerConsumer(AsyncWebsocketConsumer):
    """
    General WebSocket consumer for tracker-wide communication.
    Handles general notifications and system-wide messages.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    async def connect(self):
        """
        Handle WebSocket connection.
        """
        try:
            # Get user from scope (requires authentication middleware)
            self.user = self.scope.get('user')
            
            if not self.user or not self.user.is_authenticated:
                logger.warning("Unauthenticated user attempted to connect to general tracker WebSocket")
                await self.close()
                return
            
            await self.accept()
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to tracker WebSocket',
                'user': self.user.username
            }))
            
            logger.info(f"User {self.user.username} connected to general tracker WebSocket")
            
        except Exception as e:
            logger.error(f"Error in general WebSocket connect: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        try:
            logger.info(f"User {self.user.username if self.user else 'Unknown'} disconnected from general tracker WebSocket")
        except Exception as e:
            logger.error(f"Error in general WebSocket disconnect: {str(e)}")

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.
        """
        try:
            message_data = json.loads(text_data)
            
            # Validate message format
            is_valid, error_message = validate_websocket_message(message_data)
            if not is_valid:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': error_message
                }))
                return
            
            message_type = message_data['type']
            
            # Route message to appropriate handler
            if message_type == 'ping':
                await self.handle_ping()
            elif message_type == 'test_message':
                await self.handle_test_message(message_data)
            else:
                logger.warning(f"Unhandled message type in general consumer: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in general WebSocket message")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error handling general WebSocket message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    async def handle_ping(self):
        """
        Handle ping message for connection health check.
        """
        try:
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': str(timezone.now())
            }))
            
        except Exception as e:
            logger.error(f"Error handling ping: {str(e)}")

    async def handle_test_message(self, message_data):
        """
        Handle test message for debugging.
        """
        try:
            await self.send(text_data=json.dumps({
                'type': 'test_response',
                'message': f"Received test message: {message_data.get('message', '')}",
                'user': self.user.username,
                'timestamp': str(timezone.now())
            }))
            
        except Exception as e:
            logger.error(f"Error handling test message: {str(e)}")


class ProjectRoomConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for project-based real-time communication.
    Handles joining/leaving project rooms and broadcasting notifications.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = None
        self.project_room_group_name = None
        self.user = None

    async def connect(self):
        """
        Handle WebSocket connection.
        """
        try:
            # Extract project ID from URL route
            self.project_id = self.scope['url_route']['kwargs']['project_id']
            self.project_room_group_name = get_project_room_name(self.project_id)
            
            # Get user from scope (requires authentication middleware)
            self.user = self.scope.get('user')
            
            if not self.user or not self.user.is_authenticated:
                logger.warning(f"Unauthenticated user attempted to connect to project {self.project_id}")
                await self.close()
                return
            
            # Verify user has access to this project
            has_project_access = await self.check_project_access()
            if not has_project_access:
                logger.warning(f"User {self.user.username} denied access to project {self.project_id}")
                await self.close()
                return
            
            # Join project room group
            await self.channel_layer.group_add(
                self.project_room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': f'Connected to project {self.project_id}',
                'project_id': self.project_id,
                'user': self.user.username
            }))
            
            logger.info(f"User {self.user.username} connected to project {self.project_id} WebSocket")
            
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        try:
            if self.project_room_group_name:
                # Leave project room group
                await self.channel_layer.group_discard(
                    self.project_room_group_name,
                    self.channel_name
                )
                
                logger.info(f"User {self.user.username if self.user else 'Unknown'} disconnected from project {self.project_id} WebSocket")
                
        except Exception as e:
            logger.error(f"Error in WebSocket disconnect: {str(e)}")

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.
        """
        try:
            message_data = json.loads(text_data)
            
            # Validate message format
            is_valid, error_message = validate_websocket_message(message_data)
            if not is_valid:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': error_message
                }))
                return
            
            message_type = message_data['type']
            
            # Route message to appropriate handler
            if message_type == 'typing_start':
                await self.handle_typing_start(message_data)
            elif message_type == 'typing_stop':
                await self.handle_typing_stop(message_data)
            elif message_type == 'ping':
                await self.handle_ping()
            elif message_type == 'test_project_message':
                await self.handle_test_project_message(message_data)
            else:
                logger.warning(f"Unhandled message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in WebSocket message")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    async def handle_typing_start(self, message_data):
        """
        Handle typing start indicator.
        """
        try:
            # Broadcast typing indicator to project room
            await self.channel_layer.group_send(
                self.project_room_group_name,
                {
                    'type': 'send_typing_indicator',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': True
                }
            )
            
            logger.info(f"User {self.user.username} started typing in project {self.project_id}")
            
        except Exception as e:
            logger.error(f"Error handling typing start: {str(e)}")

    async def handle_typing_stop(self, message_data):
        """
        Handle typing stop indicator.
        """
        try:
            # Broadcast typing stop to project room
            await self.channel_layer.group_send(
                self.project_room_group_name,
                {
                    'type': 'send_typing_indicator',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': False
                }
            )
            
            logger.info(f"User {self.user.username} stopped typing in project {self.project_id}")
            
        except Exception as e:
            logger.error(f"Error handling typing stop: {str(e)}")

    async def handle_ping(self):
        """
        Handle ping message for connection health check.
        """
        try:
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': str(timezone.now())
            }))
            
        except Exception as e:
            logger.error(f"Error handling ping: {str(e)}")

    async def handle_test_project_message(self, message_data):
        """
        Handle test message for project room debugging.
        """
        try:
            await self.send(text_data=json.dumps({
                'type': 'test_project_response',
                'message': f"Received test message in project {self.project_id}: {message_data.get('message', '')}",
                'project_id': self.project_id,
                'user': self.user.username,
                'timestamp': str(timezone.now())
            }))
            
        except Exception as e:
            logger.error(f"Error handling test project message: {str(e)}")

    # Group message handlers
    async def send_notification(self, event):
        """
        Send notification to WebSocket client.
        """
        try:
            notification_type = event['notification_type']
            notification_data = event['data']
            
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'notification_type': notification_type,
                'data': notification_data
            }))
            
            logger.info(f"Notification sent to user {self.user.username}: {notification_type}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")

    async def send_typing_indicator(self, event):
        """
        Send typing indicator to WebSocket client.
        """
        try:
            # Don't send typing indicator back to the user who is typing
            if event['user_id'] != self.user.id:
                await self.send(text_data=json.dumps({
                    'type': 'typing_indicator',
                    'user_id': event['user_id'],
                    'username': event['username'],
                    'is_typing': event['is_typing']
                }))
                
        except Exception as e:
            logger.error(f"Error sending typing indicator: {str(e)}")

    async def send_activity_update(self, event):
        """
        Send activity log update to WebSocket client.
        """
        try:
            activity_data = event['activity_data']
            
            await self.send(text_data=json.dumps({
                'type': 'activity_update',
                'activity_data': activity_data
            }))
            
            logger.info(f"Activity update sent to user {self.user.username}")
            
        except Exception as e:
            logger.error(f"Error sending activity update: {str(e)}")

    @database_sync_to_async
    def check_project_access(self):
        """
        Check if the current user has access to the project.
        Users have access if they own the project or are involved in its bugs.
        """
        try:
            project = get_object_or_404(Project, id=self.project_id)
            
            # Check if user is project owner
            if project.project_owner == self.user:
                return True
            
            # Check if user is assigned to any bugs in the project
            if project.project_bugs.filter(assigned_to_user=self.user).exists():
                return True
            
            # Check if user created any bugs in the project
            if project.project_bugs.filter(created_by_user=self.user).exists():
                return True
            
            return False
            
        except Project.DoesNotExist:
            logger.error(f"Project {self.project_id} does not exist")
            return False
        except Exception as e:
            logger.error(f"Error checking project access: {str(e)}")
            return False

    # TODO: Add WebSocket connection rate limiting per user
    # TODO: Implement WebSocket message size validation
    # TODO: Add WebSocket connection timeout handling
    # TODO: Implement WebSocket reconnection logic

