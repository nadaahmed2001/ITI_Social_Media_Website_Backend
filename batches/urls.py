from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (ProgramViewSet, TrackViewSet, BatchViewSet, 
                    StudentBatchViewSet, DepartmentViewSet, UploadNationalIDView, AllProgramsViewSet,AllTracksByProgramView)

router = DefaultRouter()
router.register(r'programs', ProgramViewSet, basename="program")
router.register(r'all-programs', AllProgramsViewSet, basename="all-programs")
router.register(r'tracks', TrackViewSet, basename="track") #Displays track of the department of the logged-in supervisor only
# router.register(r'all-tracks', AllTracksByProgramView.as_view(), name='all-tracks-by-program')
router.register(r'batches', BatchViewSet, basename="batch")
router.register(r'student-batches', StudentBatchViewSet, basename="student-batch")
router.register(r'departments', DepartmentViewSet, basename="department")

# Do NOT register UploadNationalIDView in the router (since it's an APIView)
urlpatterns = [
    path('', include(router.urls)),
    path('upload-national-id/', UploadNationalIDView.as_view(), name='upload-national-id'),
    path('all-tracks/', AllTracksByProgramView.as_view(), name='all-tracks-by-program'),
]
