from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, JsonResponse
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Define a more robust health check endpoint
def health_check(request):
    """
    Health check endpoint that returns OK to indicate the service is running
    """
    from django.db import connection
    
    # Test database connection
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception as e:
        db_ok = False
    
    status = {
        "status": "healthy" if db_ok else "unhealthy",
        "db_connection": "ok" if db_ok else "failed"
    }
    
    status_code = 200 if db_ok else 500
    return JsonResponse(status, status=status_code)

# Helper function to safely include URLs
def safe_include(urlconf_module):
    try:
        return include(urlconf_module)
    except ModuleNotFoundError as e:
        logger.warning(f"Failed to include {urlconf_module}: {str(e)}")
        # Return a simple pattern that shows an error message
        return path('', lambda r: JsonResponse({"error": f"Module {urlconf_module} is not available"}, status=501))

# Debug auth check endpoint
def debug_auth(request):
    """Simple endpoint to verify user authentication status"""
    return HttpResponse(
        f"Authenticated: {request.user.is_authenticated}, "
        f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}"
    )

# Main URL patterns
urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    
    # API endpoints grouped by module
    path("api/users/", include("users.urls")),
    path("api/batches/", include("batches.urls")),
    path("api/posts/", include("posts.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/", include("core.urls")),
    
    # Health check and monitoring endpoints
    path("health/", health_check, name="health_check"),
    
    # Debugging endpoints
    path("api/debug/auth/", debug_auth, name="debug_auth"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
