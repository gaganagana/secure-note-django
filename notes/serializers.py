"""
Serializers for the SecureNote REST API.

In an interview, explain:
- Serializers validate incoming request payloads and serialize Python dictionary/model data into JSON.
- To keep the architecture completely explicit and easy to trace, encryption and decryption
  are NOT hidden inside custom serializer methods.
- The API views explicitly call `encrypt_text()` when saving, and `decrypt_text()` when reading.
"""

from rest_framework import serializers
from .models import Note


class NoteSerializer(serializers.Serializer):
    """
    Serializer used for validating incoming note data and formatting outgoing JSON responses.
    The 'content' field represents plaintext in API interactions;
    the database field 'encrypted_content' stores the encrypted ciphertext.
    """
    id = serializers.IntegerField(read_only=True)
    owner = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=200, required=True)
    category = serializers.ChoiceField(choices=Note.CATEGORY_CHOICES, default='Personal')
    content = serializers.CharField(required=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
