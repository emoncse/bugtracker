"""
Main URL configuration for the tracker application.
Includes versioned API URLs and landing page.
"""

from django.urls import path, include
from .api.v1.views import landing_page

# Import versioned URL patterns
from .api.v1.urls import urlpatterns as api_v1_urlpatterns

urlpatterns = [
    # Landing page
    path('', landing_page, name='landing_page'),
    
    # Include versioned API URLs
    path('', include(api_v1_urlpatterns)),
]

