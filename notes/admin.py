"""
Django Admin configuration for Note model.

In an interview, explain:
- To protect user privacy, `encrypted_content` is displayed as read-only ciphertext.
- The admin interface does NOT decrypt private notes, respecting user privacy and the
  principle of least privilege (administrators see metadata, not plaintext secrets).
"""

from django.contrib import admin
from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at', 'updated_at')
    search_fields = ('title', 'owner__username')
    readonly_fields = ('encrypted_content', 'created_at', 'updated_at')
    ordering = ('-updated_at',)

    fieldsets = (
        ('Note Metadata', {
            'fields': ('title', 'owner', 'category')
        }),
        ('Cryptographic Storage', {
            'fields': ('encrypted_content',),
            'description': (
                '<div style="color: #666; font-style: italic; margin-bottom: 10px;">'
                'Security Notice: This content is encrypted using Fernet symmetric encryption before '
                'database storage. Ciphertext is displayed for administrative inspection without exposing plaintext.'
                '</div>'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
