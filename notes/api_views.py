"""
REST API views for SecureNote using Django REST Framework.

In an interview, explain:
- We use APIView for explicit, transparent request handling.
- `permission_classes = [IsAuthenticated]` guarantees that unauthenticated requests are rejected (401).
- Every database query filters by `owner=request.user` to guarantee strict authorization.
- Encryption (`encrypt_text`) and decryption (`decrypt_text`) are called explicitly right inside the views.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Note
from .serializers import NoteSerializer
from .utils import encrypt_text, decrypt_text, DecryptionError


class NoteListCreateAPIView(APIView):
    """
    API endpoint to list authenticated user's notes (GET)
    or create a new encrypted note (POST).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Query only the authenticated user's notes
        notes = Note.objects.filter(owner=request.user)

        # Explicitly decrypt each note's content before serialization
        data = []
        for note in notes:
            try:
                decrypted = decrypt_text(note.encrypted_content)
            except DecryptionError:
                decrypted = "[Decryption Error: Key mismatch or corrupted data]"

            data.append({
                'id': note.id,
                'owner': note.owner.username,
                'title': note.title,
                'category': note.category,
                'content': decrypted,
                'created_at': note.created_at,
                'updated_at': note.updated_at,
            })

        serializer = NoteSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = NoteSerializer(data=request.data)
        if serializer.is_valid():
            title = serializer.validated_data['title']
            category = serializer.validated_data.get('category', 'Personal')
            plain_content = serializer.validated_data['content']

            # EXPLICIT ENCRYPTION: Encrypt plaintext before saving to database
            cipher_text = encrypt_text(plain_content)

            note = Note.objects.create(
                owner=request.user,
                title=title,
                category=category,
                encrypted_content=cipher_text
            )

            response_data = {
                'id': note.id,
                'owner': note.owner.username,
                'title': note.title,
                'category': note.category,
                'content': plain_content,
                'created_at': note.created_at,
                'updated_at': note.updated_at,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NoteDetailAPIView(APIView):
    """
    API endpoint to retrieve (GET), update (PUT), or delete (DELETE)
    a specific note by ID.
    Enforces strict ownership authorization.
    """
    permission_classes = [IsAuthenticated]

    def get_note(self, pk, user):
        """Helper to fetch note only if owned by the authenticated user."""
        try:
            return Note.objects.get(pk=pk, owner=user)
        except Note.DoesNotExist:
            return None

    def get(self, request, pk):
        note = self.get_note(pk, request.user)
        if not note:
            return Response(
                {'detail': 'Note not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # EXPLICIT DECRYPTION: Decrypt ciphertext for authorized owner
        try:
            plain_content = decrypt_text(note.encrypted_content)
        except DecryptionError:
            plain_content = "[Decryption Error: Key mismatch or corrupted data]"

        response_data = {
            'id': note.id,
            'owner': note.owner.username,
            'title': note.title,
            'category': note.category,
            'content': plain_content,
            'created_at': note.created_at,
            'updated_at': note.updated_at,
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        note = self.get_note(pk, request.user)
        if not note:
            return Response(
                {'detail': 'Note not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = NoteSerializer(data=request.data)
        if serializer.is_valid():
            plain_content = serializer.validated_data['content']

            # EXPLICIT RE-ENCRYPTION: Encrypt updated content
            note.title = serializer.validated_data['title']
            note.category = serializer.validated_data.get('category', note.category)
            note.encrypted_content = encrypt_text(plain_content)
            note.save()

            response_data = {
                'id': note.id,
                'owner': note.owner.username,
                'title': note.title,
                'category': note.category,
                'content': plain_content,
                'created_at': note.created_at,
                'updated_at': note.updated_at,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        note = self.get_note(pk, request.user)
        if not note:
            return Response(
                {'detail': 'Note not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND
            )

        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
