from rest_framework import serializers
from .models import Department, Program, Track, Batch, StudentBatch

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"

class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = "__all__"

class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = "__all__"

class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = "__all__"

class StudentBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentBatch
        fields = "__all__"
