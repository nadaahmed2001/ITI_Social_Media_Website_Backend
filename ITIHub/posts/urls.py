from django.urls import path
from .views import PostListView, PostDetailView, PostEditView , PostDeleteView ,CommentEditView , CommentDeleteView , AddReaction , RemoveReaction ,ViewReactionsView  , ViewCommentReactions 
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', PostListView.as_view(), name='post-list'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('edit/<int:pk>/', PostEditView.as_view(), name='post_edit'), 
    path('delete/<int:pk>/',PostDeleteView.as_view(),name='post_delete'),
    path('comment/edit/<int:pk>/', CommentEditView.as_view(), name='comment_edit'),
    path('comment/delete/<int:pk>/', CommentDeleteView.as_view(), name='comment_delete'),
    path('react/<int:post_id>/<str:reaction_type>/', AddReaction.as_view(), name='add-reaction'),
    path('react/<int:post_id>/remove/', RemoveReaction.as_view(), name='remove-reaction'),
    path('viewReactions/<int:post_id>/', ViewReactionsView.as_view(), name='view-reactions'),
    # start


    
    path('react/comment/<int:comment_id>/<str:reaction_type>/', AddReaction.as_view(), name='add-comment-reaction'),
    path('react/comment/<int:comment_id>/remove/', RemoveReaction.as_view(), name='remove-comment-reaction'),
    path('view-reactions/comment/<int:comment_id>/', ViewCommentReactions.as_view(), name='view-comment-reactions'),
    #end
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

