
from django.urls import path
from .views import (PostListCreateView, PostDetailView, CommentCreateView,
                    CommentDetailView, AddReaction, RemoveReaction , ListCommentsView , 
                    ReplyCreateView , ReplyDetailView ,PostReactionsView , CommentEditView , 
                    CommentDeleteView ,CommentReactionsView) 

urlpatterns = [
    path('', PostListCreateView.as_view(), name='post-list-create'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),  # Use post_id
    path('<int:post_id>/comment/', CommentCreateView.as_view(), name='comment-create'),  # Use post_id
    # path('comment/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('<int:post_id>/comments/', ListCommentsView.as_view(), name='post-comments'),
    path('<int:post_id>/react/remove/', RemoveReaction.as_view(), name='post-remove-reaction'),
    path('comment/<int:comment_id>/react/remove/', RemoveReaction.as_view(), name='comment-remove-reaction'),
    path('<int:post_id>/react/<str:reaction_type>/', AddReaction.as_view(), name='post-react'),
    path('comment/<int:comment_id>/react/<str:reaction_type>/', AddReaction.as_view(), name='comment-react'),
    path('<int:post_id>/reactions/', PostReactionsView.as_view(), name='post-reactions'),
    path('comment/edit/<int:post_id>/<int:comment_id>/', CommentEditView.as_view(), name='comment_edit'),
    path('comment/delete/<int:post_id>/<int:comment_id>/', CommentDeleteView.as_view(), name='comment_delete'),
    path('comment/<int:comment_id>/reactions/', CommentReactionsView.as_view(), name='comment-reactions'),
    path('comments/<int:comment_id>/replies/', ReplyCreateView.as_view(), name='reply-create'),
    path('replies/<int:pk>/', ReplyDetailView.as_view(), name='reply-detail'),
]