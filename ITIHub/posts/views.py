from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Post, Comment, Reaction, Attachment
from .serializers import PostSerializer, CommentSerializer, ReactionSerializer , EditCommentSerializer, DeleteCommentSerializer
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


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination  # Add this line
    
    def get_queryset(self):
        queryset = Post.objects.all() \
            .select_related('author__profile') \
            .prefetch_related('attachments') \
            .order_by('-created_on')
        
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

    def get_queryset(self):
        # Get the post using the 'post_id' in the URL
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id)\
                             .select_related('author__profile')\
                             .order_by('-created_on')

@method_decorator(csrf_exempt, name="dispatch")
class PostReactionsView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated
    
    def get(self, request, post_id):
        """Retrieve all reactions for a specific post"""
        try:
            # Get the post instance
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        # Filter reactions by post
        reactions = Reaction.objects.filter(post=post)

        # Serialize the reactions
        serializer = ReactionSerializer(reactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    ## Edit Comment API
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
