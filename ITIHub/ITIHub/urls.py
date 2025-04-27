from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import ProfileSearchView
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "healthy"})


urlpatterns = [
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
    path('health/', health_check, name='health_check'),
]
