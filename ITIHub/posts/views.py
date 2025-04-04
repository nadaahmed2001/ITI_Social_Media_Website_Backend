from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Post, Comment, Reaction
from .serializers import PostSerializer, CommentSerializer, ReactionSerializer
from users.decorators import student_or_supervisor_required
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from users.permissions import IsStudentOrSupervisor
from notifications.models import Notification
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Post.objects.all().order_by('-created_on')
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

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

#  Like & Dislike Post (Toggle)
# class PostLikeDislikeView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk, action):
#         post = get_object_or_404(Post, pk=pk)

#         if action == "like":
#             post.toggle_like(request.user)
#             if post.author != request.user:  
#                 Notification.objects.create(
#                     recipient=post.author,
#                     sender=request.user,
#                     notification_type="reaction",
#                     reaction_type="like", 
#                     related_content_type=ContentType.objects.get_for_model(post),
#                     related_object_id=post.id
#                 )

#         elif action == "dislike":
#             post.toggle_dislike(request.user)
#             if post.author != request.user:
#                 Notification.objects.create(
#                     recipient=post.author,
#                     sender=request.user,
#                     notification_type="reaction",
#                     reaction_type="dislike",
#                     related_content_type=ContentType.objects.get_for_model(post),
#                     related_object_id=post.id
#                 )

#         else:
#             return Response(
#                 {"error": f"Invalid action '{action}'. Allowed actions: ['like', 'dislike']."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         return Response({"message": f"Post {action}d successfully."}, status=status.HTTP_200_OK)

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
        return Comment.objects.filter(post_id=post_id).order_by('-created_on')  # Assuming you have a 'created_on' field
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