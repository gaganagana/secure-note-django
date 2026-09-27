"""
Root URL configuration for SecureNote project.

In an interview, explain:
- ROOT_URLCONF points to this file.
- It delegates application-specific routes to `notes.urls` via `include()`.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('notes.urls')),
]
