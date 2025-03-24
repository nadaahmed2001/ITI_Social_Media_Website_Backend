from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("supervisor_pages/", include("batches.urls")),
    path("users/", include("users.urls")),   # Authentication URLs
    # path("", include("django.contrib.auth.urls")),  # Default login/logout/password reset
    path('admin/', admin.site.urls),
    path('chat/', include('chat.urls')),
]

