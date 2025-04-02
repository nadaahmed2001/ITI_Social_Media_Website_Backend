from projects.models import Project
from .serializers import ProjectSerializer
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from users.models import Profile
from projects.models import Project, Tag
from rest_framework import status


# Create your views here.
class IsProjectOwnerOrReadOnly(BasePermission):
    """
    Custom permission to allow owners of the project to edit it, while others can only view it.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the project or is making a read-only request
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user.profile

# Project API
class ProjectAPI(APIView):
    permission_classes = [IsAuthenticated]

    # def get(self, request, pk=None):
    #     if pk:
    #         # Retrieve a specific project
    #         project = get_object_or_404(Project, pk=pk)
    #         serializer = ProjectSerializer(project)
    #         return Response(serializer.data)
    #     else:
    #         # List all projects
    #         projects = Project.objects.all()
    #         serializer = ProjectSerializer(projects, many=True)
    #         return Response(serializer.data)
    def get(self, request, pk=None):
        if pk:
            # Retrieve a specific project (remains the same)
            project = get_object_or_404(Project, pk=pk)
            # Optional: Add permission check if needed even for GET specific
            # self.check_object_permissions(request, project)
            serializer = ProjectSerializer(project, context={'request': request}) # Pass context if serializer needs it
            return Response(serializer.data)
        else:
            # List projects, potentially filtered
            queryset = Project.objects.all()
            owner_id = request.query_params.get('owner', None) # Check for 'owner' query parameter
            if owner_id:
                # Filter by owner if the parameter is provided
                queryset = queryset.filter(owner__id=owner_id)
            # Optional: Add more filters here if needed (e.g., by tag)

            serializer = ProjectSerializer(queryset, many=True, context={'request': request}) # Pass context
            return Response(serializer.data)

    def post(self, request):
        # Add the owner to the data before creating the project
        data = request.data.copy()
        owner = request.user.profile  # Get the profile of the logged-in user
        data['owner'] = owner.id  # Set the 'owner' to the profile ID (UUID)

        # Handle the file upload for featured_image
        if 'featured_image' in request.FILES:
            data['featured_image'] = request.FILES['featured_image']

        # Handle tags in the request data
        tags_data = request.data.get('tags', [])
        tags = []

        # Iterate over tag names to either fetch existing tags or create new ones
        for tag_name in tags_data:
            tag_name_lower = tag_name.strip().lower()  # Normalize to lowercase
            tag, created = Tag.objects.get_or_create(name=tag_name_lower)
            tags.append(tag)

        # Add tags to the data dictionary for saving the project
        data['tags'] = [tag.id for tag in tags]

        # Create the project with the provided data
        serializer = ProjectSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()  # Save the project instance
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        # Update an existing project
        project = get_object_or_404(Project, pk=pk)
        
        # Check if the user is the owner of the project
        if project.owner != request.user.profile:
            return Response({"detail": "You do not have permission to update this project."}, status=status.HTTP_403_FORBIDDEN)
        
        # Extract and process tags from the request data
        tags_data = request.data.get('tags', [])
        tag_objects = []

        # Loop through the provided tags and check if they exist, otherwise create them
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tag_objects.append(tag)
        
        # Add the tags to the request data (this ensures they are saved with the project)
        request.data['tags'] = [tag.id for tag in tag_objects]

        # Pass the 'request' object to the serializer context
        serializer = ProjectSerializer(project, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            # Check if the user entered an existing title
            if Project.objects.filter(owner=request.user.profile, title__iexact=serializer.validated_data['title']).exists():
                return Response({"detail": "A project with this title already exists."}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # Delete a project
        project = get_object_or_404(Project, pk=pk)
        
        # Check if the user is the owner of the project
        if project.owner != request.user.profile:
            return Response({"detail": "You do not have permission to delete this project."}, status=status.HTTP_403_FORBIDDEN)
            
        # Check if the user is the owner of the project
        if project.owner != request.user.profile:
            return Response({"detail": "You do not have permission to delete this project."}, status=status.HTTP_403_FORBIDDEN)
        
        project.delete()
        return Response({"message": "Project deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class ProjectTagAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        # Add a tag to the project
        project = get_object_or_404(Project, pk=pk)
        tag_id = request.data.get('tag_id')
        tag = get_object_or_404(Tag, pk=tag_id)

        # Check if the tag is already added to the project
        if tag not in project.tags.all():
            project.tags.add(tag)
            return Response({"message": "Tag added successfully."}, status=status.HTTP_201_CREATED)

        return Response({"message": "Tag is already added to this project."}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # Remove a tag from the project
        project = get_object_or_404(Project, pk=pk)
        tag_id = request.data.get('tag_id')
        tag = get_object_or_404(Tag, pk=tag_id)

        # Check if the tag is associated with the project
        if tag in project.tags.all():
            project.tags.remove(tag)
            return Response({"message": "Tag removed successfully."}, status=status.HTTP_200_OK)

        return Response({"message": "Tag is not associated with this project."}, status=status.HTTP_400_BAD_REQUEST)

class TagAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new tag
        """
        name = request.data.get('name')
        if not name:
            return Response({"message": "Tag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the tag already exists
        if Tag.objects.filter(name__iexact=name).exists():
            return Response({"message": "Tag with this name already exists."}, status=status.HTTP_400_BAD_REQUEST)

        tag = Tag.objects.create(name=name)
        return Response({"message": "Tag created successfully.", "tag": {"id": tag.id, "name": tag.name}}, status=status.HTTP_201_CREATED)

    def get(self, request, pk=None):
        """
        Get a specific tag by its ID or list all tags if no ID is provided
        """
        if pk:
            tag = get_object_or_404(Tag, pk=pk)
            return Response({"id": tag.id, "name": tag.name}, status=status.HTTP_200_OK)

        # List all tags
        tags = Tag.objects.all()
        tag_list = [{"id": tag.id, "name": tag.name} for tag in tags]
        return Response(tag_list, status=status.HTTP_200_OK)
        
    def put(self, request, pk):
        """
        Update a tag
        """
        tag = get_object_or_404(Tag, pk=pk)
        name = request.data.get('name')

        if not name:
            return Response({"message": "Tag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the tag name already exists
        if Tag.objects.filter(name__iexact=name).exists():
            return Response({"message": "Tag with this name already exists."}, status=status.HTTP_400_BAD_REQUEST)

        tag.name = name
        tag.save()
        return Response({"message": "Tag updated successfully.", "tag": {"id": tag.id, "name": tag.name}}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """
        Delete a tag
        """
        tag = get_object_or_404(Tag, pk=pk)
        tag.delete()
        return Response({"message": "Tag deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class ContributorAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        """
        Get a list of contributors for a specific project.
        """
        project = get_object_or_404(Project, pk=pk)
        contributors = project.contributors.all()
        contributor_data = [{"id": contributor.id, "username": contributor.username} for contributor in contributors]
        
        return Response(contributor_data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        """
        Add a contributor to the project by username.
        """
        project = get_object_or_404(Project, pk=pk)
        username = request.data.get('username')

        if not username:
            return Response({"message": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        contributor = get_object_or_404(Profile, username=username)

        if contributor == project.owner:
            return Response({"message": "The project owner cannot be added as a contributor."}, status=status.HTTP_400_BAD_REQUEST)

        if contributor not in project.contributors.all():
            project.contributors.add(contributor)
            return Response({"message": "Contributor added successfully."}, status=status.HTTP_201_CREATED)

        return Response({"message": "Contributor is already part of this project."}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Remove a contributor from the project by username.
        """
        project = get_object_or_404(Project, pk=pk)
        username = request.data.get('username')

        if not username:
            return Response({"message": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        contributor = get_object_or_404(Profile, username=username)

        if contributor in project.contributors.all():
            project.contributors.remove(contributor)
            return Response({"message": "Contributor removed successfully."}, status=status.HTTP_200_OK)

        return Response({"message": "Contributor is not part of this project."}, status=status.HTTP_400_BAD_REQUEST)


