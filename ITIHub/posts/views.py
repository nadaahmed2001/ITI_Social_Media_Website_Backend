from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Post, Comment, Attachment
from .serializers import PostSerializer, CommentSerializer
from users.decorators import student_or_supervisor_required
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from users.permissions import IsStudentOrSupervisor

#  List & Create Posts
class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all().order_by('-created_on')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

#  Retrieve, Update, Delete a Post
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
class PostLikeDislikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, action):
        post = get_object_or_404(Post, pk=pk)
        if action == "like":
            post.toggle_like(request.user)
        elif action == "dislike":
            post.toggle_dislike(request.user)
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": f"Post {action}d successfully."}, status=status.HTTP_200_OK)

#  Add Comment
class CommentCreateView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsStudentOrSupervisor]  # Use the new permission class

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


#  Edit & Delete Comment
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
