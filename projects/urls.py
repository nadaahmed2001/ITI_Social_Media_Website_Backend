from django.urls import path
from .views import (    
    ProjectAPI,
    ContributorAPI,
    ProjectTagAPI,
    TagAPI,
    ProjectLikeToggleView,
    ProjectReviewListCreateView,
    ProjectReviewDetailView,
    ProjectFeedView
    
    
)


urlpatterns = [
    
    # Project api
    path('', ProjectAPI.as_view(), name='project_list_create_api'),  # List and Create
    
    path('feed/', ProjectFeedView.as_view(), name='project-feed'), # <-- ADD THIS

    path('<uuid:pk>/', ProjectAPI.as_view(), name='project_detail_update_delete_api'),  # Retrieve, Update, Delete
    
    # Project contributors api
    path('<uuid:pk>/contributors/', ContributorAPI.as_view(), name='manage-contributors'),
    
    # Project tags api
    path('<uuid:pk>/tags/', ProjectTagAPI.as_view(), name='add-tag'), # Add a tag to the project
    path('<uuid:pk>/tags/', ProjectTagAPI.as_view(), name='remove-tag'), # Remove a tag from the project
    
    path('tags/', TagAPI.as_view(), name='tag-list-create'),        # For POST and GET (list of tags)
    path('tags/<uuid:pk>/', TagAPI.as_view(), name='tag-detail-update-delete'),  # For GET (single tag), PUT, DELETE
    
    # Like/Unlike a Project
    path('<uuid:project_pk>/like/', ProjectLikeToggleView.as_view(), name='project-like-toggle'),

    # List/Create Reviews for a Project
    path('<uuid:project_pk>/reviews/', ProjectReviewListCreateView.as_view(), name='project-review-list-create'),

    # Retrieve/Update/Delete a specific Review
    path('<uuid:project_pk>/reviews/<uuid:id>/', ProjectReviewDetailView.as_view(), name='project-review-detail'),

]
