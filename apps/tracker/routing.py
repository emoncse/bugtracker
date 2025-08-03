from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # General tracker WebSocket
    re_path(r'ws/tracker/$', consumers.TrackerConsumer.as_asgi()),
    # Project-specific WebSocket
    re_path(r'ws/tracker/(?P<project_id>\w+)/$', consumers.ProjectRoomConsumer.as_asgi()),
    # Legacy project WebSocket (for backward compatibility)
    re_path(r'ws/project/(?P<project_id>\w+)/$', consumers.ProjectRoomConsumer.as_asgi()),
]

