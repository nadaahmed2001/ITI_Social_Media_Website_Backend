from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    
    path("supervisor_pages/", include("batches.urls")),
    path("users/", include("users.urls")),   # Authentication URLs
        # path("", include("django.contrib.auth.urls")),  # Default login/logout/password reset
    path("post/" , include('posts.urls')),
    path("api/", include([
        path("batches/", include("batches.urls")),
    ])),
]




