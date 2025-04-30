from projects.models import Project
from .serializers import ProjectSerializer, TagSerializer, ProjectReviewSerializer
from rest_framework.response import Response
from rest_framework import permissions, generics, serializers
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from users.models import Profile
from projects.models import Project, Tag, ProjectLike, ProjectReview
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count # Import Count



class ReviewPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 30




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

class ProjectFeedPagination(PageNumberPagination):
    page_size = 12 # Number of projects per page
    page_size_query_param = 'page_size'
    max_page_size = 48

# --- NEW: Project Feed View ---
class ProjectFeedView(generics.ListAPIView):
    """
    Provides a paginated list of all projects, sortable by 'created' or 'likes'.
    """
    serializer_class = ProjectSerializer
    permission_classes = [permissions.AllowAny] # Feed is public
    pagination_class = ProjectFeedPagination

    def get_queryset(self):
        queryset = Project.objects.select_related('owner__user').prefetch_related('tags', 'projectlike_set') # Optimize

        # --- Sorting Logic ---
        ordering = self.request.query_params.get('ordering', '-created') # Default to latest

        if ordering == 'likes': # Sort by most liked
            # Annotate with like count and order by it
            queryset = queryset.annotate(
                num_likes=Count('projectlike')
            ).order_by('-num_likes', '-created') # Secondary sort by date
        elif ordering == 'created': # Sort by oldest (explicitly)
             queryset = queryset.order_by('created')
        else: # Default to latest ('-created')
            queryset = queryset.order_by('-created')

        return queryset

    def get_serializer_context(self):
        # Pass request context for serializer methods (like current_user_like_id)
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

# Project API
class ProjectAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk=None):
        if pk:
            # Retrieve a specific project (remains the same)
            project = get_object_or_404(Project, pk=pk)
            # Optional: Add permission check if needed even for GET specific
            self.check_object_permissions(request, project)
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
        try:
            # Get the owner profile directly from the authenticated user
            owner_profile = request.user.profile
        except Profile.DoesNotExist:
            return Response({"detail": "User profile not found."}, status=status.HTTP_400_BAD_REQUEST)
        except AttributeError:
            return Response({"detail": "Cannot determine user profile."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the serializer with request data.
        # DO NOT manually add 'owner' to request.data here.
        # The serializer should handle 'featured_image' (if ImageField) and 'tag_names' (write_only)
        serializer = ProjectSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            try:
                # *** Pass the owner instance directly to serializer.save() ***
                serializer.save(owner=owner_profile)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Catch potential errors during save (e.g., database constraints)
                print(f"Error during serializer save: {e}") # Log the error
                # Provide a generic error message to the frontend
                return Response({"detail": "An error occurred while saving the project."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # If validation fails, return errors
            print("Serializer Errors:", serializer.errors) # Log errors for debugging
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        # Permission check (good to keep)
        if project.owner != request.user.profile:
            return Response({"detail": "You do not have permission to update this project."}, status=status.HTTP_403_FORBIDDEN)


        data_to_serialize = request.data.copy() # Work with a copy

        # If frontend sends names in 'tags' and serializer needs IDs:
        if 'tags' in data_to_serialize and isinstance(data_to_serialize['tags'], list):
            tag_objects = []
            for tag_name in data_to_serialize['tags']:
                # Assuming tag names are sent as strings
                if isinstance(tag_name, str):
                    tag, created = Tag.objects.get_or_create(name__iexact=tag_name.strip(), defaults={'name': tag_name.strip()}) # Case-insensitive get_or_create
                    tag_objects.append(tag)
                # Handle if IDs are somehow sent mixed in (less likely)
                # elif isinstance(tag_name, (int, str)) and Tag.objects.filter(pk=tag_name).exists():
                #    tag_objects.append(Tag.objects.get(pk=tag_name))
            data_to_serialize['tags'] = [tag.id for tag in tag_objects] # Replace names with IDs for serializer


        serializer = ProjectSerializer(project, data=data_to_serialize, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # If serializer validation fails, return its errors
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


class ProjectLikeToggleView(APIView):
    """ Handles Liking (POST) and Unliking (DELETE) a project. """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, project_pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=project_pk)
        like, created = ProjectLike.objects.get_or_create(user=request.user, project=project)
        if created:
            # Optionally return the new like count or just success
            return Response({"status": "liked", "like_id": like.id}, status=status.HTTP_201_CREATED)
        else:
            return Response({"status": "already_liked", "like_id": like.id}, status=status.HTTP_200_OK)

    def delete(self, request, project_pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=project_pk)
        deleted_count, _ = ProjectLike.objects.filter(user=request.user, project=project).delete()
        if deleted_count > 0:
            return Response({"status": "unliked"}, status=status.HTTP_200_OK) # Or 204
        else:
            return Response({"status": "not_liked", "detail": "You haven't liked this project."}, status=status.HTTP_404_NOT_FOUND)


# --- NEW: Project Review Views ---
class ProjectReviewListCreateView(generics.ListCreateAPIView):
    """ List reviews for a project or create a new review. """
    serializer_class = ProjectReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Allow reading, require auth to create
    pagination_class = ReviewPagination # Apply pagination

    def get_queryset(self):
        project_pk = self.kwargs.get('project_pk')
        # Optimize by selecting related reviewer user/profile
        return ProjectReview.objects.filter(project_id=project_pk).select_related('reviewer__profile') # Adjust if reviewer is Profile

    def get_serializer_context(self):
        # Pass request to serializer context (needed for MinimalUserSerializer potentially)
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        project = get_object_or_404(Project, pk=self.kwargs.get('project_pk'))
        # Check if user already reviewed this project (handled by unique_together, but good practice)
        if ProjectReview.objects.filter(project=project, reviewer=self.request.user).exists():
             raise serializers.ValidationError("You have already reviewed this project.") # Handled by DRF automatically due to unique_together
        # Set reviewer and project automatically
        serializer.save(reviewer=self.request.user, project=project)


class ProjectReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """ Retrieve, Update or Delete a specific review. """
    serializer_class = ProjectReviewSerializer
    permission_classes = [permissions.IsAuthenticated] # Must be logged in
    queryset = ProjectReview.objects.all() # Base queryset
    lookup_field = 'id' # Assuming review ID is passed in URL

    def get_queryset(self):
        # Further filter by project if needed, though lookup_field usually suffices
        project_pk = self.kwargs.get('project_pk')
        return super().get_queryset().filter(project_id=project_pk)

    def check_object_permissions(self, request, obj):
        # Ensure only the reviewer can modify/delete their review
        super().check_object_permissions(request, obj)
        if request.method not in permissions.SAFE_METHODS and obj.reviewer != request.user:
            self.permission_denied(request, message="You can only modify or delete your own reviews.")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class ProjectTagAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
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
        contributor_data = [{"id": contributor.id, "username": contributor.username, "profile_picture": contributor.profile_picture} for contributor in contributors]
        
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


