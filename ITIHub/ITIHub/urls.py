from django.http import JsonResponse
from django.urls import path, include
from django.contrib import admin

def health_check(request):
    """Health check endpoint for Railway"""
    return JsonResponse({"status": "healthy"})

urlpatterns = [
    # Add this at the beginning of your urlpatterns list
    path('health/', health_check, name='health_check'),
    
    # Keep your existing paths
    path("admin/", admin.site.urls),  # Admin panel
    
    # Authentication & Users
    path("users/", include("users.urls")),  

    # API Endpoints
    path("api/", include([
        path("supervisor/", include("batches.urls")),  
        path("chat/", include("chat.urls")),  
        path("notifications/", include("notifications.urls")),  
        path("posts/", include("posts.urls")),
        path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('projects/', include('projects.urls')),
        path('search/profiles/', ProfileSearchView.as_view(), name='profile-search'),

        
    ])),
]
