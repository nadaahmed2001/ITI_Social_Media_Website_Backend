from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Post, Comment, Reaction, Reply
from .serializers import PostSerializer, CommentSerializer, ReactionSerializer , EditCommentSerializer, DeleteCommentSerializer, ReplySerializer
from users.decorators import student_or_supervisor_required
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from users.permissions import IsStudentOrSupervisor
from notifications.models import Notification
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser 
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count
from django.core.exceptions import PermissionDenied



class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10 # Number of posts per page (match frontend ITEMS_PER_PAGE)
    page_size_query_param = 'page_size'
    max_page_size = 50 # Max items per page client can request


@method_decorator(csrf_exempt, name="dispatch")

class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        sort = self.request.query_params.get('sort', 'recent')
        queryset = Post.objects.annotate(
            total_reactions=Count('reaction'),
            total_comments=Count('comments')
        )

        if sort == 'recent':
            queryset = queryset.order_by('-created_on')
        elif sort == 'relevant':
            queryset = queryset.order_by('-total_reactions', '-total_comments')

        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        return queryset


@method_decorator(csrf_exempt, name="dispatch")
class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser] # Add Parsers for potential file uploads in update


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
    parser_classes = [JSONParser] # Add Parsers


    def perform_create(self, serializer):
        # Pass author and ensure post is correctly associated (serializer expects post_id)
        post_id = self.kwargs.get('post_id') # Get post_id from URL kwargs
        post_instance = get_object_or_404(Post, pk=post_id) # Ensure post exists
        serializer.save(author=self.request.user, post=post_instance) # Pass post instance


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]


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
    # parser_classes = [JSONParser]

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


@method_decorator(csrf_exempt, name="dispatch")
class RemoveReaction(APIView):
    permission_classes = [IsAuthenticated]
    # parser_classes = [JSONParser]

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
    # parser_classes = [JSONParser]

    def get_queryset(self):
        # Get the post using the 'post_id' in the URL
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id).order_by('-created_on')  # Assuming you have a 'created_on' field


@method_decorator(csrf_exempt, name="dispatch")
class PostReactionsView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated
    # parser_classes = [JSONParser]
    
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


class ReplyCreateView(generics.CreateAPIView):
    serializer_class = ReplySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        comment = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
        serializer.save(author=self.request.user, comment=comment)

class ReplyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Reply.objects.all()
    serializer_class = ReplySerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied("You don't have permission to edit this reply")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("You don't have permission to delete this reply")
        super().perform_destroy(instance)