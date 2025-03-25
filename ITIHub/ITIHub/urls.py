from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    
    path("supervisor_pages/", include("batches.urls")),
    path("users/", include("users.urls")),   # Authentication URLs
    
  
    path("api/", include([
        path("batches/", include("batches.urls")),
        path("users/", include("users.urls")),
    ])),
]
