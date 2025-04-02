from django.urls import path
from .views import (PostListCreateView, PostDetailView, CommentCreateView,
                    CommentDetailView, AddReaction, RemoveReaction)

urlpatterns = [
    path('', PostListCreateView.as_view(), name='post-list-create'),
    path('<int:post_id>/', PostDetailView.as_view(), name='post-detail'),  # Use post_id
    path('<int:post_id>/comment/', CommentCreateView.as_view(), name='comment-create'),  # Use post_id
    path('comment/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),

    path('<int:post_id>/react/remove/', RemoveReaction.as_view(), name='post-remove-reaction'),
    path('comment/<int:comment_id>/react/remove/', RemoveReaction.as_view(), name='comment-remove-reaction'),
    path('<int:post_id>/react/<str:reaction_type>/', AddReaction.as_view(), name='post-react'),
    path('comment/<int:comment_id>/react/<str:reaction_type>/', AddReaction.as_view(), name='comment-react'),


   
]
