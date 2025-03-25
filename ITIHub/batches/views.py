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
from rest_framework import viewsets
from .models import Department, StudentBatch, Batch, Program, Track, UnverifiedNationalID, VerifiedNationalID
from .serializers import DepartmentSerializer, StudentBatchSerializer
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
import csv




class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

class ProgramViewSet(viewsets.ModelViewSet):
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get the department where the logged-in user is the supervisor
        department = Department.objects.filter(supervisor=self.request.user).first()
        
        if not department:
            return Program.objects.none()  # Return empty queryset if no department
        
        return Program.objects.filter(department=department)

class TrackViewSet(viewsets.ModelViewSet):
    serializer_class = TrackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get the department where the logged-in user is the supervisor
        department = Department.objects.filter(supervisor=self.request.user).first()
        
        if not department:
            return Track.objects.none()  # Return empty queryset if no department

        # Get programs in that department
        programs = Program.objects.filter(department=department)

        return Track.objects.filter(program__in=programs)


class BatchViewSet(viewsets.ModelViewSet):
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        supervisor = self.request.user  # Get logged-in supervisor

        # Get the department where the supervisor is assigned
        department = Department.objects.filter(supervisor=supervisor).first()
        if not department:
            return Batch.objects.none()  # Return empty queryset if supervisor has no department

        # Get batches only for programs in this department
        batches = Batch.objects.filter(program__department=department)

        # Filter by program_id if provided
        program_id = self.request.query_params.get("program_id")
        if program_id:
            batches = batches.filter(program_id=program_id)

        # Filter by track_id if provided
        track_id = self.request.query_params.get("track_id")
        if track_id:
            batches = batches.filter(track_id=track_id)

        return batches


    def create(self, request, *args, **kwargs):
        supervisor = request.user  # Get logged-in supervisor
        program_id = request.data.get("program_id")  # Get Program ID from request
        track_id = request.data.get("track_id")  # Get Track ID from request

        # Validate program and track
        try:
            program = Program.objects.get(id=program_id)
            track = Track.objects.get(id=track_id, program=program)  # Ensure track belongs to the program
        except Program.DoesNotExist:
            return Response({"error": "Program not found"}, status=status.HTTP_404_NOT_FOUND)
        except Track.DoesNotExist:
            return Response({"error": "Track not found or does not belong to the specified program"}, status=status.HTTP_404_NOT_FOUND)

        # Create the batch with program and track assigned
        batch = Batch.objects.create(
            name=request.data.get("name"),
            supervisor=supervisor,
            program=program,
            track=track
        )

        return Response(BatchSerializer(batch).data, status=status.HTTP_201_CREATED)


class StudentBatchViewSet(viewsets.ModelViewSet):
    queryset = StudentBatch.objects.all()
    serializer_class = StudentBatchSerializer
    permission_classes = [IsAuthenticated]




class UploadNationalIDView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Handles the upload of a CSV file containing national IDs.
        - Extracts and saves them to `UnverifiedNationalID`.
        """
        file = request.FILES.get('file')
        batch_id = request.data.get("batch_id")  # Get batch_id from the request

        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not batch_id:
            return Response({"error": "Batch ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            batch = Batch.objects.get(id=batch_id)
        except Batch.DoesNotExist:
            return Response({"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            national_ids = [row[0].strip() for row in reader if row]  # Extract national IDs from CSV

            created_count = 0
            for national_id in national_ids:
                if not UnverifiedNationalID.objects.filter(national_id=national_id).exists():
                    UnverifiedNationalID.objects.create(national_id=national_id, batch=batch)
                    created_count += 1
                else :
                    print(f"National ID {national_id} already exists")
                    # Make a new instance of the StudentBatch model (if not already exists)
                    student_batch, created = StudentBatch.objects.get_or_create(national_id=national_id, batch=batch)
                    if created:
                        print(f"StudentBatch instance created for {national_id}")
                        

            return Response({"message": f"{created_count} National IDs added successfully!"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
