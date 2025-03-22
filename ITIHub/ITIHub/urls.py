from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('supervisor/', include('batches.urls')),
    path('chat/', include('chat.urls')),
]
