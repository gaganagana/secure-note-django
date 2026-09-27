"""
Comprehensive unit and integration test suite for SecureNote.

In an interview, explain:
- Tests verify business logic, security constraints, and data integrity.
- TestCase runs each test in an isolated database transaction, rolling back afterwards.
- We explicitly verify that raw database fields store ciphertext, not plaintext.
- We verify that unauthorized access attempts receive HTTP 403 / 404 status codes.
"""

from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from .models import Note
from .utils import encrypt_text, decrypt_text, get_fernet, DecryptionError


class SecureNoteTests(TestCase):
    def setUp(self):
        """Set up test users and client."""
        self.client = Client()

        # Create two distinct test users to test authorization boundaries
        self.alice = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='Password123!'
        )
        self.bob = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='Password123!'
        )

        self.plain_title = "Alice Secret Study Notes"
        self.plain_content = "Study Django MVT architecture and AES-128 Fernet encryption."
        self.category = "Study"

    # 1. Password Hashing Verification
    def test_passwords_are_hashed_not_plaintext(self):
        """Verify Django stores passwords as PBKDF2 hashes, never plaintext."""
        alice_db = User.objects.get(username='alice')
        self.assertNotEqual(alice_db.password, 'Password123!')
        self.assertTrue(alice_db.password.startswith('pbkdf2_sha256$'))
        self.assertTrue(alice_db.check_password('Password123!'))
        self.assertFalse(alice_db.check_password('WrongPassword'))

    # 2. Note Creation and Direct Database Inspection (Ciphertext Verification)
    def test_note_creation_stores_ciphertext_in_database(self):
        """
        Verify that creating a note encrypts the content so that the database
        contains Fernet ciphertext, NOT the original plaintext.
        """
        self.client.login(username='alice', password='Password123!')

        response = self.client.post(reverse('note_create'), {
            'title': self.plain_title,
            'category': self.category,
            'content': self.plain_content,
        })
        self.assertEqual(response.status_code, 302)  # Redirects to detail view

        # Inspect database record directly using ORM
        note = Note.objects.get(owner=self.alice, title=self.plain_title)
        
        # PROVE THAT PLAINTEXT IS NOT STORED
        self.assertNotEqual(note.encrypted_content, self.plain_content)
        self.assertNotIn("Study Django", note.encrypted_content)
        
        # PROVE THAT CIPHERTEXT IS A VALID FERNET BASE64 TOKEN
        self.assertTrue(note.encrypted_content.startswith('gAAAAA'))
        
        # PROVE DECRYPTION RECOVERS THE EXACT ORIGINAL CONTENT
        decrypted = decrypt_text(note.encrypted_content)
        self.assertEqual(decrypted, self.plain_content)

    # 3. Owner Can View Decrypted Note
    def test_owner_can_access_and_view_decrypted_note(self):
        """Verify the owner receives HTTP 200 and the rendered HTML contains decrypted text."""
        note = Note.objects.create(
            owner=self.alice,
            title=self.plain_title,
            category=self.category,
            encrypted_content=encrypt_text(self.plain_content)
        )

        self.client.login(username='alice', password='Password123!')
        response = self.client.get(reverse('note_detail', kwargs={'pk': note.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plain_title)
        self.assertContains(response, self.plain_content)

    # 4. Strict Authorization: User B Cannot Access User A's Note
    def test_unauthorized_user_cannot_access_another_users_note(self):
        """Verify User B receives HTTP 403 Forbidden when attempting to view User A's note."""
        note = Note.objects.create(
            owner=self.alice,
            title=self.plain_title,
            category=self.category,
            encrypted_content=encrypt_text(self.plain_content)
        )

        # Login as Bob (User B)
        self.client.login(username='bob', password='Password123!')

        # Attempt to access Alice's note
        response = self.client.get(reverse('note_detail', kwargs={'pk': note.pk}))
        self.assertEqual(response.status_code, 403)

        # Attempt to edit Alice's note
        edit_response = self.client.get(reverse('note_update', kwargs={'pk': note.pk}))
        self.assertEqual(edit_response.status_code, 403)

        # Attempt to delete Alice's note
        delete_response = self.client.post(reverse('note_delete', kwargs={'pk': note.pk}))
        self.assertEqual(delete_response.status_code, 403)

        # Verify note is still in the database intact
        self.assertTrue(Note.objects.filter(pk=note.pk).exists())

    # 5. Note Update and Re-encryption
    def test_owner_can_update_and_reencrypt_note(self):
        """Verify updating a note updates the ciphertext in the database."""
        note = Note.objects.create(
            owner=self.alice,
            title="Initial Title",
            category="Ideas",
            encrypted_content=encrypt_text("Initial secret content")
        )

        self.client.login(username='alice', password='Password123!')

        updated_text = "Updated and re-encrypted secret content."
        response = self.client.post(reverse('note_update', kwargs={'pk': note.pk}), {
            'title': 'Updated Title',
            'category': 'Work',
            'content': updated_text,
        })
        self.assertEqual(response.status_code, 302)

        # Refresh from database
        note.refresh_from_db()
        self.assertEqual(note.title, 'Updated Title')
        self.assertEqual(note.category, 'Work')
        self.assertNotEqual(note.encrypted_content, updated_text)
        self.assertEqual(decrypt_text(note.encrypted_content), updated_text)

    # 6. Note Deletion
    def test_owner_can_delete_note(self):
        """Verify note deletion permanently removes the record."""
        note = Note.objects.create(
            owner=self.alice,
            title="To Delete",
            category="Personal",
            encrypted_content=encrypt_text("Temporary note")
        )

        self.client.login(username='alice', password='Password123!')
        response = self.client.post(reverse('note_delete', kwargs={'pk': note.pk}))
        self.assertEqual(response.status_code, 302)

        self.assertFalse(Note.objects.filter(pk=note.pk).exists())

    # 7. DecryptionError on Corrupted Ciphertext
    def test_corrupted_ciphertext_raises_decryption_error(self):
        """Verify that tampering with ciphertext triggers DecryptionError."""
        corrupted_token = "gAAAAABinvalidcorruptedtoken1234567890=="
        with self.assertRaises(DecryptionError):
            decrypt_text(corrupted_token)

    # 8. REST API: Unauthenticated Access Rejected (401 or 403)
    def test_api_unauthenticated_access_rejected(self):
        """Verify that accessing /api/notes/ without credentials rejects with 401 or 403."""
        response = self.client.get(reverse('api_note_list_create'))
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    # 9. REST API: Authenticated User Can Create and List Notes
    def test_api_authenticated_user_can_create_and_list_notes(self):
        """Verify creating and retrieving notes via REST API."""
        self.client.login(username='alice', password='Password123!')

        # POST to /api/notes/
        post_response = self.client.post(
            reverse('api_note_list_create'),
            data={'title': 'API Note', 'category': 'Work', 'content': 'Secret via API'},
            content_type='application/json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(post_response.data['title'], 'API Note')
        self.assertEqual(post_response.data['content'], 'Secret via API')

        # Verify DB stored ciphertext
        created_note = Note.objects.get(title='API Note')
        self.assertNotEqual(created_note.encrypted_content, 'Secret via API')
        self.assertEqual(decrypt_text(created_note.encrypted_content), 'Secret via API')

        # GET /api/notes/
        get_response = self.client.get(reverse('api_note_list_create'))
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_response.data), 1)
        self.assertEqual(get_response.data[0]['content'], 'Secret via API')

    # 10. REST API: User B Cannot Retrieve User A's Note (404)
    def test_api_user_cannot_retrieve_another_users_note(self):
        """Verify User B cannot access User A's note via API (returns 404)."""
        note = Note.objects.create(
            owner=self.alice,
            title="Alice API Private",
            category="Personal",
            encrypted_content=encrypt_text("Top secret")
        )

        # Login as Bob
        self.client.login(username='bob', password='Password123!')

        response = self.client.get(reverse('api_note_detail', kwargs={'pk': note.pk}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 11. Key Configuration Verification
    def test_missing_fernet_key_raises_improperly_configured(self):
        """Verify that get_fernet raises ImproperlyConfigured if FERNET_KEY is missing."""
        with patch.dict('os.environ', {'FERNET_KEY': ''}):
            with self.assertRaises(ImproperlyConfigured):
                get_fernet()

    def test_invalid_fernet_key_raises_improperly_configured(self):
        """Verify that get_fernet raises ImproperlyConfigured if FERNET_KEY is malformed."""
        with patch.dict('os.environ', {'FERNET_KEY': 'not-a-valid-base64-key'}):
            with self.assertRaises(ImproperlyConfigured):
                get_fernet()
