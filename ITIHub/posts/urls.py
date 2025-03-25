from django.urls import path
from .views import PostListView, PostDetailView, PostEditView , PostDeleteView ,CommentEditView , CommentDeleteView , AddLike, Dislike 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', PostListView.as_view(), name='post-list'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('edit/<int:pk>/', PostEditView.as_view(), name='post_edit'), 
    path('delete/<int:pk>/',PostDeleteView.as_view(),name='post_delete'),
    path('comment/edit/<int:pk>/', CommentEditView.as_view(), name='comment_edit'),
    path('comment/delete/<int:pk>/', CommentDeleteView.as_view(), name='comment_delete'),
    path('react/<int:pk>/like' , AddLike.as_view(),name='like'),
    path('react/<int:pk>/dislike' ,Dislike.as_view(),name="dislike"),
    # path('react/<int:pk>/', ReactToPost.as_view(), name='react'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



# Serve media files in development

# urlpatterns = [
#     path('', PostListView.as_view(), name='post-list'),
#     path('<int:pk>/', login_required(PostDetailView.as_view()), name='post-detail'),
#     path('edit/<int:pk>/', login_required(PostEditView.as_view()), name='post_edit'), 
#     path('delete/<int:pk>/',login_required(PostDeleteView.as_view()),name='post_delete'),
#     path('comment/edit/<int:pk>/', login_required(CommentEditView.as_view()), name='comment_edit'),
#     path('comment/delete/<int:pk>/', login_required(CommentDeleteView.as_view()), name='comment_delete'),
# ]