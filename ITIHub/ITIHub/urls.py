from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# Define a more robust health check endpoint
def health_check(request):
    """
    Health check endpoint that returns OK to indicate the service is running
    """
    from django.http import JsonResponse
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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/batches/", include("batches.urls")),
    path("api/groups/", include("groups.urls")),
    path("api/posts/", include("posts.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/chat/", include("chat.urls")),  # Make sure this line exists
    path("health/", health_check, name="health_check"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Add a debug URL to check auth
urlpatterns += [
    path("api/debug/auth/", 
         lambda request: HttpResponse(f"Authenticated: {request.user.is_authenticated}, User: {request.user.username if request.user.is_authenticated else 'Anonymous'}"), 
         name="debug_auth"),
]
