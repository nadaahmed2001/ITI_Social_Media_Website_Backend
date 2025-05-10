from projects.models import Project
from .serializers import ProjectSerializer, TagSerializer, ProjectReviewSerializer, ContributorProfileSerializer
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
from django.db import transaction # Import transaction



class ReviewPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 30

class ProjectFeedPagination(PageNumberPagination):
    page_size = 12 
    page_size_query_param = 'page_size'
    max_page_size = 48

class IsProjectOwnerOrReadOnly(BasePermission):
    """
    Custom permission to allow owners of the project to edit it, while others can only view it.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the project or is making a read-only request
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user.profile



# --- NEW: Project Feed View ---
class ProjectFeedView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.AllowAny] # Feed is public
    pagination_class = ProjectFeedPagination

    def get_queryset(self):
        # Optimization: Select related owner user and profile, prefetch tags and likes
        queryset = Project.objects.select_related('owner__user').prefetch_related('tags', 'projectlike_set')

        ordering = self.request.query_params.get('ordering', '-created')

        if ordering == 'likes':
            queryset = queryset.annotate(num_likes=Count('projectlike')).order_by('-num_likes', '-created')
        elif ordering == 'created':
            queryset = queryset.order_by('created')
        else:
            queryset = queryset.order_by('-created')

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

# --- Project Detail/List/Create/Update/Delete View ---
class ProjectAPI(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk=None):
        if pk:
            project = get_object_or_404(Project.objects.select_related('owner__user'), pk=pk)
            serializer = ProjectSerializer(project, context={'request': request})
            return Response(serializer.data)
        else:
            # Listing projects filtered by owner
            queryset = Project.objects.select_related('owner__user').prefetch_related('tags')
            owner_id = request.query_params.get('owner', None)
            if owner_id:
                # Assuming owner_id is the Profile UUID
                queryset = queryset.filter(owner__id=owner_id)
            else:
                # Maybe default to logged-in user's projects if no owner specified? Or return all?
                # For now, returning all if no owner specified.
                pass

            # Add pagination if needed for this list variant
            paginator = ProjectFeedPagination() # Reuse feed pagination or create another
            page = paginator.paginate_queryset(queryset.order_by('-created'), request, view=self)
            if page is not None:
                serializer = ProjectSerializer(page, many=True, context={'request': request})
                return paginator.get_paginated_response(serializer.data)

            # Fallback if pagination is not used
            serializer = ProjectSerializer(queryset.order_by('-created'), many=True, context={'request': request})
            return Response(serializer.data)

    def post(self, request):
        try: owner_profile = request.user.profile
        except (Profile.DoesNotExist, AttributeError): return Response({"detail": "User profile not found or accessible."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ProjectSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try: serializer.save(owner=owner_profile); return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e: print(f"Error during serializer save: {e}"); return Response({"detail": "Error saving project."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else: print("Serializer Errors:", serializer.errors); return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if project.owner != request.user.profile: return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProjectSerializer(project, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid(): serializer.save(); return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if project.owner != request.user.profile: return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        project.delete(); return Response(status=status.HTTP_204_NO_CONTENT)



class ProjectLikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, project_pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=project_pk); like, created = ProjectLike.objects.get_or_create(user=request.user, project=project);
        if created: return Response({"status": "liked", "like_id": like.id}, status=status.HTTP_201_CREATED)
        else: return Response({"status": "already_liked", "like_id": like.id}, status=status.HTTP_200_OK)
    def delete(self, request, project_pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=project_pk); deleted_count, _ = ProjectLike.objects.filter(user=request.user, project=project).delete();
        if deleted_count > 0: return Response({"status": "unliked"}, status=status.HTTP_200_OK)
        else: return Response({"status": "not_liked", "detail": "You haven't liked this project."}, status=status.HTTP_404_NOT_FOUND)


# --- Project Review Views ---
class ProjectReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = ReviewPagination

    def get_queryset(self):
        project_pk = self.kwargs.get('project_pk')
        # *** DEBUGGING STEP: Simplify select_related ***
        # Try fetching only the reviewer (User) first
        # If this works, the issue is accessing reviewer.profile
        return ProjectReview.objects.filter(project_id=project_pk).select_related('reviewer') # REMOVED __profile
        # Original: return ProjectReview.objects.filter(project_id=project_pk).select_related('reviewer__profile').order_by('-created')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        print("--- Review perform_create START ---")
        project_pk = self.kwargs.get('project_pk')
        print(f"Project PK: {project_pk}")
        project = get_object_or_404(Project, pk=project_pk)
        print(f"Found Project: {project.id}")
        reviewer_user = self.request.user.profile
        print(f"Reviewer User: {reviewer_user.username} (ID: {reviewer_user.id})")

        # --- DEBUG: Test serializer initialization ---
        try:
            # This uses the validated_data passed to perform_create
            print(f"Serializer instance valid: {serializer.is_valid()}") # Should be true if called from ListCreateAPIView after validation
            print("Serializer data before save:", serializer.validated_data)
        except Exception as e:
            print(f"--- ERROR during serializer check before DB query: {type(e).__name__} - {e} ---")
            raise e # Re-raise to see traceback

        # --- DEBUG: Test DB filter ---
        existing_review = None
        try:
            existing_review = ProjectReview.objects.filter(project=project, reviewer=reviewer_user).first() # Use first() instead of exists() for more info
            if existing_review:
                print(f"DEBUG: Found existing review: ID {existing_review.id}") # Log if found
                raise serializers.ValidationError({"detail": "You have already reviewed this project."})
            else:
                print("DEBUG: No existing review found for this user/project.") # Log if not found

        except Exception as e:
            print(f"--- ERROR during ProjectReview.objects.filter: {type(e).__name__} - {e} ---")
            raise e # Re-raise to see traceback

        # --- Try saving ---
        try:
            print(f"Attempting serializer.save with reviewer={reviewer_user.id}, project={project.id}")
            serializer.save(reviewer=reviewer_user, project=project)
            print("--- Review perform_create SAVE successful ---")
        except Exception as e:
            print(f"--- ERROR during serializer.save in perform_create: {type(e).__name__} - {e} ---")
            raise e




class ProjectReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ProjectReview.objects.select_related('reviewer__user')
    lookup_field = 'id'

    def get_queryset(self):
        project_pk = self.kwargs.get('project_pk')
        return super().get_queryset().filter(project_id=project_pk)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        try:
            request_profile = request.user.profile
        except (Profile.DoesNotExist, AttributeError):
            self.permission_denied(request, message="Cannot determine your profile for permission check.")
        if request.method not in permissions.SAFE_METHODS and obj.reviewer != request_profile:
            self.permission_denied(request, message="You can only modify or delete your own reviews.")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @transaction.atomic # Ensure DB operation is committed
    def update(self, request, *args, **kwargs):
        print("--- ProjectReviewDetailView Simplified UPDATE ---")
        partial = kwargs.pop('partial', False) # Check if it's a PATCH request
        instance = self.get_object() # Get the review instance
        print(f"--- Instance BEFORE manual update: ID={instance.id}, Body='{instance.body}', Vote='{instance.vote}'")

        # Manually update fields based on request data
        new_body = request.data.get('body', instance.body if partial else '')
        new_vote = request.data.get('vote', instance.vote if partial else None)

        # Basic validation
        if not partial and not new_body.strip() and not new_vote:
            return Response({"detail": "Review body or vote is required."}, status=status.HTTP_400_BAD_REQUEST)
        # Add validation for vote value if provided
        if new_vote is not None and new_vote not in dict(ProjectReview.VOTE_TYPE):
            return Response({"vote": ["Invalid vote value."]}, status=status.HTTP_400_BAD_REQUEST)


        instance.body = new_body
        instance.vote = new_vote
        print(f"--- Instance attributes set to: Body='{instance.body}', Vote='{instance.vote}'") # Log before save

        try:
            # Manually save the instance
            # Try saving without update_fields first to rule that out
            # instance.save(update_fields=['body', 'vote', 'modified'])
            instance.save()
            print(f"--- Manual instance.save() CALLED successfully ---") # Log right after save

            # Reload from DB to confirm persistence
            instance.refresh_from_db()
            print(f"--- Instance AFTER manual save & refresh: ID={instance.id}, Body='{instance.body}', Vote='{instance.vote}'")

            # Manually serialize the updated instance
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"--- ERROR during manual instance.save(): {type(e).__name__} - {e}")
            # Return a 500 error with details if possible
            return Response({"detail": f"Error saving review: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @transaction.atomic # Ensure DB operation is committed
    def destroy(self, request, *args, **kwargs):
        print("--- ProjectReviewDetailView Simplified DESTROY ---")
        instance = self.get_object()
        instance_id = instance.id # Store ID for logging after delete
        print(f"--- Instance to delete manually: ID={instance_id}, Reviewer={instance.reviewer.username}")
        try:
            # Manually delete the instance
            instance.delete()
            print(f"--- Manual instance.delete() called for ID={instance_id}")
            # Verify deletion
            exists = ProjectReview.objects.filter(id=instance_id).exists()
            print(f"--- Instance exists in DB after manual delete attempt: {exists}")
            # Return 204 No Content on successful deletion
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            print(f"--- ERROR during manual instance.delete(): {type(e).__name__} - {e}")
            # Return a 500 error with details if possible
            return Response({"detail": f"Error deleting review: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



class ProjectTagAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # parser_classes = [JSONParser] # Usually not needed

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if project.owner != request.user.profile: return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        tag_id = request.data.get('tag_id')
        if not tag_id: return Response({"message": "tag_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        tag = get_object_or_404(Tag, pk=tag_id)
        project.tags.add(tag)
        return Response({"message": "Tag added successfully."}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if project.owner != request.user.profile: return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        tag_id = request.data.get('tag_id') # Assuming tag ID is sent in body for DELETE
        if not tag_id: return Response({"message": "tag_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        tag = get_object_or_404(Tag, pk=tag_id)
        if tag in project.tags.all():
            project.tags.remove(tag); return Response({"message": "Tag removed successfully."}, status=status.HTTP_200_OK)
        else: return Response({"message": "Tag is not associated with this project."}, status=status.HTTP_400_BAD_REQUEST)


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
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk): # pk here is project ID
        project = get_object_or_404(Project.objects.prefetch_related('contributors__user'), pk=pk) # Optimize
        # Use serializer for consistency
        serializer = ContributorProfileSerializer(project.contributors.all(), many=True)
        return Response(serializer.data)

    def post(self, request, pk): # pk here is project ID
        project = get_object_or_404(Project, pk=pk)
        if project.owner != request.user.profile: return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        username = request.data.get('username')
        if not username: return Response({"message": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
        try: contributor_profile = Profile.objects.select_related('user').get(user__username__iexact=username) # Find profile via username
        except Profile.DoesNotExist: return Response({"message": f"User with username '{username}' not found."}, status=status.HTTP_404_NOT_FOUND)
        if contributor_profile == project.owner: return Response({"message": "Owner cannot be added as contributor."}, status=status.HTTP_400_BAD_REQUEST)
        if project.contributors.filter(pk=contributor_profile.pk).exists(): return Response({"message": "Contributor already part of project."}, status=status.HTTP_400_BAD_REQUEST)
        project.contributors.add(contributor_profile)
        return Response({"message": "Contributor added successfully."}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk): # pk here is project ID
        project = get_object_or_404(Project, pk=pk)
        if project.owner != request.user.profile: return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        username = request.data.get('username')
        if not username: return Response({"message": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
        try: contributor_profile = Profile.objects.get(user__username__iexact=username)
        except Profile.DoesNotExist: return Response({"message": f"User with username '{username}' not found."}, status=status.HTTP_404_NOT_FOUND)
        if project.contributors.filter(pk=contributor_profile.pk).exists():
            project.contributors.remove(contributor_profile); return Response({"message": "Contributor removed successfully."}, status=status.HTTP_200_OK)
        else: return Response({"message": "Contributor is not part of this project."}, status=status.HTTP_400_BAD_REQUEST)

