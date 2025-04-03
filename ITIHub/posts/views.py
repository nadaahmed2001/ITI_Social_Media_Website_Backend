from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Post, Comment, Reaction
from .serializers import PostSerializer, CommentSerializer , ReactionSerializer
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.edit import UpdateView, DeleteView
from django.views.generic import ListView
from .forms import CommentForm

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
        Reaction.objects.create(
            user=request.user, 
            post=target if isinstance(target, Post) else None, 
            comment=target if isinstance(target, Comment) else None, 
            reaction_type=reaction_type
        )

        return Response({"message": "Reaction added successfully"}, status=status.HTTP_201_CREATED)

#   RemoveReaction API
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
    
class ListCommentsView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get the post using the 'post_id' in the URL
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id).order_by('-created_on')  # Assuming you have a 'created_on' field
    
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
    

class CommentEditView(LoginRequiredMixin,UserPassesTestMixin,UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'comment_edit.html'

    def get_success_url(self):
        return reverse_lazy('post-detail', kwargs={'pk': self.object.post.pk})

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author
    
class CommentDeleteView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model = Comment
    template_name = 'comment_delete.html'

    def get_success_url(self):
        return reverse_lazy('post-detail', kwargs={'pk': self.object.post.pk})
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author