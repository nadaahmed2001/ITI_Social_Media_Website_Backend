from django.urls import path
from .views import PostListCreateView, PostDetailView, PostLikeDislikeView, CommentCreateView, CommentDetailView

urlpatterns = [
    path('', PostListCreateView.as_view(), name='post-list-create'),  #  List & Create Posts
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),  #  Retrieve, Update, Delete Post
    path('<int:pk>/comment/', CommentCreateView.as_view(), name='comment-create'),  #  Add Comment
    path('comment/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),  #  Edit/Delete Comment
    path('<int:pk>/react/<str:action>/', PostLikeDislikeView.as_view(), name='post-like-dislike'),  #  Like/Dislike
]
