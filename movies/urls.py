from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='movies.index'),
    path('<int:id>/', views.show, name='movies.show'),
    path('<int:id>/review/create/', views.create_review, name='movies.create_review'),
    path('<int:id>/review/<int:review_id>/edit/', views.edit_review, name='movies.edit_review'),
    path('<int:id>/review/<int:review_id>/delete/', views.delete_review, name='movies.delete_review'),
    path('<int:id>/rating/submit/', views.submit_rating, name='movies.submit_rating'),
    path('petitions/', views.petitions_index, name='movies.petitions'),
    path('petitions/create/', views.create_petition, name='movies.create_petition'),
    path('petitions/<int:petition_id>/upvote/', views.upvote_petition, name='movies.upvote_petition'),
    path('popularity-map/', views.popularity_map, name='movies.popularity_map'),
    path('popularity-map/data/', views.popularity_map_data, name='movies.popularity_map_data'),
]
