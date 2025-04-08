# # posts/urls.py
# from django.urls import path
# # Import all necessary views from .views
# from .views import (
#     PostListCreateView, PostDetailView,
#     CommentCreateView, ListCommentsView, CommentEditView, CommentDeleteView,
#     # CommentDetailView, # Uncomment if you create/need this view
#     AddReaction, RemoveReaction, PostReactionsView, CommentReactionsView,
#     ReplyCreateView, ReplyDetailView # Add if using replies
# )

# # app_name = 'posts' # Optional: define for namespacing if needed

# urlpatterns = [
#     # --- Posts ---
#     # List posts or Create a new post
#     path('', PostListCreateView.as_view(), name='post-list-create'),
#     # Retrieve, Update (PUT/PATCH), or Delete a specific post
#     path('<uuid:pk>/', PostDetailView.as_view(), name='post-detail'), # Use pk for Post ID

#     # --- Comments (related to posts) ---
#     # List comments for a specific post
#     path('<uuid:post_id>/comments/', ListCommentsView.as_view(), name='list-comments'),
#     # Create a new comment under a specific post
#     path('<uuid:post_id>/comment/', CommentCreateView.as_view(), name='comment-create'),
#     # Edit a specific comment (needs post_id for context/lookup in view)
#     path('<uuid:post_id>/comments/<uuid:pk>/edit/', CommentEditView.as_view(), name='comment-edit'), # Use pk for Comment ID
#     # Delete a specific comment (needs post_id for context/lookup in view)
#     path('<uuid:post_id>/comments/<uuid:pk>/delete/', CommentDeleteView.as_view(), name='comment-delete'), # Use pk for Comment ID
#     # Optional: Retrieve a specific comment detail
#     # path('<uuid:post_id>/comments/<uuid:pk>/', CommentDetailView.as_view(), name='comment-detail'),

#     # --- Reactions ---
#     # Add/Update reaction to a post
#     path('<uuid:post_id>/react/<str:reaction_type>/', AddReaction.as_view(), name='post-react'),
#     # Remove reaction from a post
#     path('<uuid:post_id>/react/remove/', RemoveReaction.as_view(), name='post-remove-reaction'),
#     # Add/Update reaction to a comment
#     path('comment/<uuid:comment_id>/react/<str:reaction_type>/', AddReaction.as_view(), name='comment-react'),
#     # Remove reaction from a comment
#     path('comment/<uuid:comment_id>/react/remove/', RemoveReaction.as_view(), name='comment-remove-reaction'),
#     # List reactions for a post
#     path('<uuid:post_id>/reactions/', PostReactionsView.as_view(), name='post-reactions'),
#     # List reactions for a comment
#     path('comment/<uuid:comment_id>/reactions/', CommentReactionsView.as_view(), name='comment-reactions'),

#     # --- Replies (related to comments) ---
#     # Create a reply under a specific comment
#     path('comments/<uuid:comment_id>/replies/', ReplyCreateView.as_view(), name='reply-create'),
#     # Retrieve, Update, or Delete a specific reply
#     path('replies/<uuid:pk>/', ReplyDetailView.as_view(), name='reply-detail'), # Use pk for Reply ID
# ]

# posts/urls.py
from django.urls import path
# Import all necessary views
from .views import (
    PostListCreateView, PostDetailView,
    CommentCreateView, ListCommentsView, CommentEditView, CommentDeleteView,
    # CommentDetailView, # Uncomment if you create/need this view
    AddReaction, RemoveReaction, PostReactionsView, CommentReactionsView,
    ReplyCreateView, ReplyDetailView # Add if using replies
)

# app_name = 'posts' # Optional: define for namespacing if needed

urlpatterns = [
    # --- Posts ---
    path('', PostListCreateView.as_view(), name='post-list-create'),
    # Change path converter to <int:pk> for Post ID
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),

    # --- Comments (related to posts) ---
    # Change path converter to <int:post_id>
    path('<int:post_id>/comments/', ListCommentsView.as_view(), name='list-comments'),
    # Change path converter to <int:post_id>
    path('<int:post_id>/comment/', CommentCreateView.as_view(), name='comment-create'),
    # Change path converters to <int:post_id> and <int:pk> (for Comment ID)
    path('<int:post_id>/comments/<int:pk>/edit/', CommentEditView.as_view(), name='comment-edit'),
    # Change path converters to <int:post_id> and <int:pk> (for Comment ID)
    path('<int:post_id>/comments/<int:pk>/delete/', CommentDeleteView.as_view(), name='comment-delete'),

    # --- Reactions ---
    # Change path converter to <int:post_id>
    path('<int:post_id>/react/<str:reaction_type>/', AddReaction.as_view(), name='post-react'),
    # Change path converter to <int:post_id>
    path('<int:post_id>/react/remove/', RemoveReaction.as_view(), name='post-remove-reaction'),
    # Change path converter to <int:comment_id>
    path('comment/<int:comment_id>/react/<str:reaction_type>/', AddReaction.as_view(), name='comment-react'),
    # Change path converter to <int:comment_id>
    path('comment/<int:comment_id>/react/remove/', RemoveReaction.as_view(), name='comment-remove-reaction'),
    # Change path converter to <int:post_id>
    path('<int:post_id>/reactions/', PostReactionsView.as_view(), name='post-reactions'),
    # Change path converter to <int:comment_id>
    path('comment/<int:comment_id>/reactions/', CommentReactionsView.as_view(), name='comment-reactions'),
    path('<int:post_id>/comment/', CommentCreateView.as_view(), name='comment-create'),


    # --- Replies (related to comments) ---
    # Change path converter to <int:comment_id>
    path('comments/<int:comment_id>/replies/', ReplyCreateView.as_view(), name='reply-create'),
    # Change path converter to <int:pk> for Reply ID
    path('replies/<int:pk>/', ReplyDetailView.as_view(), name='reply-detail'),
]