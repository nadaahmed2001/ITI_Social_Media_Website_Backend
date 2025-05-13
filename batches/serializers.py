from rest_framework import serializers
from .models import Department, Program, Track, Batch, StudentBatch

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']  # Only include fields you need

class ProgramSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Program
        fields = ['id', 'name', 'description', 'department']


class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = "__all__"
class BatchSerializer(serializers.ModelSerializer):
    program_id = serializers.IntegerField(write_only=True)
    track_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Batch
        fields = ['id', 'name', 'program_id', 'track_id', 'created_at', 'active']
        read_only_fields = ['id', 'created_at', 'active']

    def create(self, validated_data):
        program_id = validated_data.pop('program_id')
        track_id = validated_data.pop('track_id')
        request = self.context['request']
        print(f"Creating batch with program_id: {program_id}, track_id: {track_id} and supervisor: {request.user}")

        program = Program.objects.get(id=program_id)
        track = Track.objects.get(id=track_id)

        return Batch.objects.create(
            program=program,
            track=track,
            supervisor=request.user,
            **validated_data
        )



class StudentBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentBatch
        fields = "__all__"
