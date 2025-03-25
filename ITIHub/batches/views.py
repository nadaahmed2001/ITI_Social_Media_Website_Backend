from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import user_passes_test
from .models import Program, Track, Batch
from .serializers import ProgramSerializer, TrackSerializer, BatchSerializer
from rest_framework import viewsets
from .models import Department, StudentBatch
from .serializers import DepartmentSerializer, StudentBatchSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Program, Track, Batch
from .serializers import ProgramSerializer, TrackSerializer, BatchSerializer





class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]

class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = [IsAuthenticated]

class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]

class StudentBatchViewSet(viewsets.ModelViewSet):
    queryset = StudentBatch.objects.all()
    serializer_class = StudentBatchSerializer
    permission_classes = [IsAuthenticated]
