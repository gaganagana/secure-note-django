"""
Database models for SecureNote.

In an interview, explain:
- Note has a Many-to-One relationship with Django's built-in User model (ForeignKey).
- `on_delete=models.CASCADE` ensures that if a user account is deleted, all their notes are deleted too.
- `encrypted_content` stores the base64 ciphertext produced by Fernet, NOT plaintext.
"""

from django.db import models
from django.contrib.auth.models import User


class Note(models.Model):
    CATEGORY_CHOICES = [
        ('Personal', 'Personal'),
        ('Study', 'Study'),
        ('Work', 'Work'),
        ('Ideas', 'Ideas'),
        ('Journal', 'Journal'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notes',
        help_text="User who owns and has exclusive access to this note."
    )
    title = models.CharField(
        max_length=200,
        help_text="Non-sensitive title used for organization and fast indexing."
    )
    encrypted_content = models.TextField(
        help_text="Ciphertext encrypted at the application layer via Fernet before database storage."
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='Personal',
        help_text="Category classification for organizing notes."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the note was first created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the note was last updated."
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'

    def __str__(self):
        return f"{self.title} - {self.owner.username} ({self.category})"
