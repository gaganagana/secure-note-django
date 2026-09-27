"""
URL patterns for the notes app (Web views and REST API endpoints).

In an interview, explain:
- URL patterns map incoming HTTP request paths to their corresponding view functions/classes.
- Path parameters like `<int:pk>` capture variable parts of the URL as typed arguments.
- Named URL patterns (`name='...'`) enable reverse URL resolution in templates and view redirects.
"""

from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # Public & Authentication routes
    path('', views.landing_view, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Core Application routes (Authenticated)
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('notes/', views.note_list_view, name='note_list'),
    path('notes/create/', views.note_create_view, name='note_create'),
    path('notes/<int:pk>/', views.note_detail_view, name='note_detail'),
    path('notes/<int:pk>/edit/', views.note_update_view, name='note_update'),
    path('notes/<int:pk>/delete/', views.note_delete_view, name='note_delete'),

    # REST API endpoints (Django REST Framework)
    path('api/notes/', api_views.NoteListCreateAPIView.as_view(), name='api_note_list_create'),
    path('api/notes/<int:pk>/', api_views.NoteDetailAPIView.as_view(), name='api_note_detail'),
]
