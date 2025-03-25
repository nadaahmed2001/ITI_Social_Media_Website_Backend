from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, ProgramViewSet, TrackViewSet, BatchViewSet, StudentBatchViewSet

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'programs', ProgramViewSet)
router.register(r'tracks', TrackViewSet)
router.register(r'batches', BatchViewSet)
router.register(r'student-batches', StudentBatchViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
