from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Post, SavedPost, Comment, Reaction, Attachment
from .serializers import PostSerializer, CommentSerializer, ReactionSerializer , EditCommentSerializer, DeleteCommentSerializer, SavedPost, SavedPostSerializer
from users.decorators import student_or_supervisor_required
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from users.permissions import IsStudentOrSupervisor
from notifications.models import Notification
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # Number of posts per page
    page_size_query_param = 'page_size'
    max_page_size = 100


class CommentPagination(PageNumberPagination):
    page_size = 3  # Or your desired number of comments per page
    page_size_query_param = 'page_size' # Allows frontend to request different size (optional)
    max_page_size = 20 # Max comments per page


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination  # Add this line
    
    def get_queryset(self):
        # Ensure author__profile is selected
        queryset = Post.objects.all() \
            .select_related('author__profile') \
            .prefetch_related('attachments') \
            .order_by('-created_on')
        # ... filtering ...
        # return queryset
        
        if author_id := self.request.query_params.get('author'):
            queryset = queryset.filter(author_id=author_id)
        
        return queryset

    def perform_create(self, serializer):
        attachment_urls = self.request.data.getlist('attachment_urls', [])  # Changed to getlist
        post = serializer.save(author=self.request.user)
        
        for url in attachment_urls:
            is_image = any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif'])
            is_video = any(ext in url.lower() for ext in ['.mp4', '.mov'])
            
            attachment = Attachment.objects.create(
                image=url if is_image else None,
                video=url if is_video else None
            )
            post.attachments.add(attachment)
        

@method_decorator(csrf_exempt, name="dispatch")
class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return Response({"error": "You are not authorized to edit this post."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return Response({"error": "You are not authorized to delete this post."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class SavePostToggleView(APIView):
    """
    View to handle saving and unsaving a post.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id, *args, **kwargs):
        """Save a post."""
        post = get_object_or_404(Post, id=post_id)
        user = request.user

        # Create SavedPost record, get_or_create handles duplicates gracefully
        saved_post, created = SavedPost.objects.get_or_create(user=user, post=post)

        if created:
            # If created is True, the post was newly saved
            return Response({"status": "saved", "message": "Post saved successfully."}, status=status.HTTP_201_CREATED)
        else:
            # If created is False, it means the post was already saved
            return Response({"status": "already_saved", "message": "Post was already saved."}, status=status.HTTP_200_OK)

    def delete(self, request, post_id, *args, **kwargs):
        """Unsave a post."""
        post = get_object_or_404(Post, id=post_id)
        user = request.user

        # Find and delete the SavedPost record
        deleted_count, _ = SavedPost.objects.filter(user=user, post=post).delete()

        if deleted_count > 0:
            # If deleted_count > 0, the post was successfully unsaved
            return Response({"status": "unsaved", "message": "Post unsaved successfully."}, status=status.HTTP_200_OK) # Or 204 No Content
        else:
            # If deleted_count is 0, the post wasn't saved by this user
            return Response({"status": "not_found", "message": "Post was not saved by this user."}, status=status.HTTP_404_NOT_FOUND)


class SavedPostsPagination(PageNumberPagination):
    page_size = 9 # Show 9 saved posts per page
    page_size_query_param = 'page_size'
    max_page_size = 30

class SavedPostListView(generics.ListAPIView):
    """
    API View to list posts saved by the currently authenticated user.
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = SavedPostsPagination # Optional pagination

    def get_queryset(self):
        """
        Return a queryset of Post objects that the current user has saved,
        ordered by when they were saved (most recent first).
        """
        user = self.request.user
        # Filter Posts where a SavedPost entry exists linking it to the current user
        # Assumes related_name on SavedPost.user is 'saved_posts_M' (fix if different)
        # Or use the reverse relation from Post: post.saved_by_users
        # Corrected related name from SavedPost model provided: 'saved_posts_M'
        # If that name is wrong, adjust query. Let's assume it should be 'savedpost_set' or similar default if related_name is missing/wrong
        # Or filter SavedPost directly and get posts from there.

        # Safer approach: Filter SavedPost first
        saved_post_ids = SavedPost.objects.filter(user=user).order_by('-saved_on').values_list('post_id', flat=True)

        # Preserve the order from SavedPost using a Case/When expression or fetching in order
        # Fetching posts based on the ordered IDs
        # Note: This might not be the most performant for very large numbers of saved posts
        # but preserves the 'saved_on' ordering.
        ordered_posts = Post.objects.filter(id__in=list(saved_post_ids))
        # If you need to precisely match the saved_on order:
        from django.db.models import Case, When
        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(saved_post_ids)])
        queryset = Post.objects.filter(id__in=saved_post_ids).order_by(preserved_order)

        # Optimize by prefetching related data needed by PostSerializer
        return queryset.select_related('author__profile').prefetch_related('attachments')


class CommentCreateView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return Response({"error": "You are not authorized to edit this comment."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return Response({"error": "You are not authorized to delete this comment."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class AddReaction(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id=None, comment_id=None, reaction_type=None):
        if reaction_type not in dict(Reaction.REACTIONS):
            return Response({"error": "Invalid reaction type"}, status=status.HTTP_400_BAD_REQUEST)

        if post_id:
            target = get_object_or_404(Post, id=post_id)
        elif comment_id:
            target = get_object_or_404(Comment, id=comment_id)
        else:
            return Response({"error": "Invalid target"}, status=status.HTTP_400_BAD_REQUEST)

        Reaction.objects.filter(user=request.user, post=post_id, comment=comment_id).delete()
        reaction =Reaction.objects.create(
            user=request.user, 
            post=target if isinstance(target, Post) else None, 
            comment=target if isinstance(target, Comment) else None, 
            reaction_type=reaction_type
        )

        return Response({"message": "Reaction added successfully"}, status=status.HTTP_201_CREATED)

#   RemoveReaction API
@method_decorator(csrf_exempt, name="dispatch")
class RemoveReaction(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id=None, comment_id=None):
        """Removes a reaction from a post or comment"""
        if post_id:
            target = get_object_or_404(Post, id=post_id)
            Reaction.objects.filter(user=request.user, post=target).delete()
        elif comment_id:
            target = get_object_or_404(Comment, id=comment_id)
            Reaction.objects.filter(user=request.user, comment=target).delete()
        else:
            return Response({"error": "Invalid target"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": True}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name="dispatch")
class ListCommentsView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CommentPagination # <--- ADD THIS LINE


    def get_queryset(self):
        # Get the post using the 'post_id' in the URL
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id)\
                            .select_related('author__profile')\
                            .order_by('-created_on')

@method_decorator(csrf_exempt, name="dispatch") 
class PostReactionsView(APIView): 
    permission_classes = [IsAuthenticated] 
    
    def get(self, request, post_id): 
        try: 
            post = Post.objects.get(id=post_id) 
        except Post.DoesNotExist: 
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND) 

        # *** Crucial: Fetch related user and profile efficiently ***
        reactions = Reaction.objects.filter(post=post).select_related('user__profile') 

        serializer = ReactionSerializer(reactions, many=True) 
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
    
class CommentEditView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, post_id, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id, post__id=post_id)
        # comment = get_object_or_404(Comment, pk=comment_id)

        if comment.author != request.user:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = EditCommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    ## Delete Comment API
class CommentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, post_id, comment_id):
        # Fetch the comment based on post_id and comment_id
        comment = get_object_or_404(Comment, pk=comment_id, post__id=post_id)

        # Check if the user is the author of the comment
        if comment.author != request.user:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        # Validate confirmation flag before deleting
        serializer = DeleteCommentSerializer(data=request.data)
        if serializer.is_valid():
            # Confirm the deletion
            if serializer.validated_data['confirmation']:
                comment.delete()
                return Response({'detail': 'Comment deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'detail': 'Confirmation required to delete the comment.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@method_decorator(csrf_exempt, name="dispatch")
class CommentReactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, comment_id):
        """Retrieve all reactions for a specific comment"""
        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

        reactions = Reaction.objects.filter(comment=comment)
        serializer = ReactionSerializer(reactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
