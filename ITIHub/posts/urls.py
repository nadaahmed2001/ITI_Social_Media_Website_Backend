
from django.urls import path
from .views import (PostListCreateView, PostDetailView, CommentCreateView,
                    CommentDetailView, AddReaction, RemoveReaction , ListCommentsView , PostReactionsView , CommentEditView , CommentDeleteView ,CommentReactionsView) 

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
]

# from django.urls import path
# from .views import PostListCreateView, PostDetailView, CommentCreateView, CommentDetailView, AddReaction, RemoveReaction, PostCommentsView

# urlpatterns = [
#     # Post URLs
#     path('', PostListCreateView.as_view(), name='post-list-create'),
#     path('<int:post_id>/', PostDetailView.as_view(), name='post-detail'),  
#     path('<int:post_id>/edit/', PostDetailView.as_view(), name='post-edit'),  
#     path('<int:post_id>/delete/', PostDetailView.as_view(), name='post-delete'),  
#     path('<int:post_id>/comment/', CommentCreateView.as_view(), name='comment-create'),  # Create comment for a post
#     path('<int:post_id>/comments/', PostCommentsView.as_view(), name='post-comments'),  # Get comments for a post

#     # Comment URLs
#     path('comment/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),  
#     path('comment/<int:pk>/edit/', CommentDetailView.as_view(), name='comment-edit'),  
#     path('comment/<int:pk>/delete/', CommentDetailView.as_view(), name='comment-delete'),  

#     # Reaction URLs
#     path('<int:post_id>/react/remove/', RemoveReaction.as_view(), name='post-remove-reaction'),  
#     path('comment/<int:comment_id>/react/remove/', RemoveReaction.as_view(), name='comment-remove-reaction'),  
#     path('<int:post_id>/react/<str:reaction_type>/', AddReaction.as_view(), name='post-react'),  
#     path('comment/<int:comment_id>/react/<str:reaction_type>/', AddReaction.as_view(), name='comment-react'),  
# ]


