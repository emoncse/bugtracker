from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import logging

# Set up logging for WebSocket utilities
logger = logging.getLogger('tracker.websocket')


def send_websocket_notification(project_id, notification_type, notification_data):
    """
    Send a WebSocket notification to all users in a project room.
    
    Args:
        project_id (int): ID of the project to send notification to
        notification_type (str): Type of notification (bug_created, bug_updated, etc.)
        notification_data (dict): Data to send with the notification
    """
    try:
        channel_layer = get_channel_layer()
        project_room_name = get_project_room_name(project_id)
        
        notification_message = {
            'type': 'send_notification',
            'notification_type': notification_type,
            'data': notification_data
        }
        
        # Send to the project room group
        async_to_sync(channel_layer.group_send)(
            project_room_name,
            notification_message
        )
        
        logger.info(f"WebSocket notification sent to project {project_id}: {notification_type}")
        
    except Exception as e:
        logger.error(f"Failed to send WebSocket notification to project {project_id}: {str(e)}")


def send_typing_indicator(project_id, user_id, username, is_typing):
    """
    Send typing indicator to project room.
    
    Args:
        project_id (int): ID of the project
        user_id (int): ID of the user typing
        username (str): Username of the user typing
        is_typing (bool): Whether user is typing or stopped typing
    """
    try:
        channel_layer = get_channel_layer()
        project_room_name = get_project_room_name(project_id)
        
        typing_message = {
            'type': 'send_typing_indicator',
            'user_id': user_id,
            'username': username,
            'is_typing': is_typing
        }
        
        # Send to the project room group
        async_to_sync(channel_layer.group_send)(
            project_room_name,
            typing_message
        )
        
        action = "started" if is_typing else "stopped"
        logger.info(f"Typing indicator sent to project {project_id}: {username} {action} typing")
        
    except Exception as e:
        logger.error(f"Failed to send typing indicator to project {project_id}: {str(e)}")


def send_activity_stream(project_id, activity_data):
    """
    Send activity log update to project room for real-time activity streaming.
    
    Args:
        project_id (int): ID of the project
        activity_data (dict): Activity log data to stream
    """
    try:
        channel_layer = get_channel_layer()
        project_room_name = get_project_room_name(project_id)
        
        activity_message = {
            'type': 'send_activity_update',
            'activity_data': activity_data
        }
        
        # Send to the project room group
        async_to_sync(channel_layer.group_send)(
            project_room_name,
            activity_message
        )
        
        activity_type = activity_data.get('activity_type', 'unknown')
        logger.info(f"Activity stream update sent to project {project_id}: {activity_type}")
        
    except Exception as e:
        logger.error(f"Failed to send activity stream to project {project_id}: {str(e)}")


def get_project_room_name(project_id):
    """
    Get the standardized room name for a project.
    
    Args:
        project_id (int): ID of the project
        
    Returns:
        str: Standardized room name for the project
    """
    return f"project_{project_id}"


def validate_websocket_message(message_data):
    """
    Validate incoming WebSocket message data.
    
    Args:
        message_data (dict): Message data to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        required_fields = ['type']
        
        if not isinstance(message_data, dict):
            return False, "Message data must be a dictionary"
        
        for field in required_fields:
            if field not in message_data:
                return False, f"Missing required field: {field}"
        
        valid_message_types = [
            'join_project_room',
            'leave_project_room',
            'typing_start',
            'typing_stop',
            'ping'
        ]
        
        if message_data['type'] not in valid_message_types:
            return False, f"Invalid message type: {message_data['type']}"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating WebSocket message: {str(e)}")
        return False, f"Validation error: {str(e)}"


# TODO: Add WebSocket connection rate limiting
# TODO: Implement WebSocket message encryption for sensitive data
# TODO: Add WebSocket connection health monitoring
# TODO: Implement WebSocket message queuing for offline users

