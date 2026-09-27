"""
Encryption utilities for SecureNote.

This module provides dedicated helper functions for application-level symmetric encryption
and decryption using the Python `cryptography` library's Fernet implementation.

Key concept for interviews:
- Fernet uses AES-128-CBC for encryption and HMAC-SHA256 for integrity verification.
- Encryption is TWO-WAY (reversible with the key), whereas password hashing is ONE-WAY.
"""

import os
from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured


class DecryptionError(Exception):
    """
    Raised when ciphertext cannot be decrypted due to corruption,
    tampering, or encryption with a mismatched key.
    """
    pass


def get_fernet() -> Fernet:
    """
    Retrieves the FERNET_KEY from the environment and returns an active Fernet cipher instance.
    Raises ImproperlyConfigured if the key is missing or invalid.
    No automatic or fallback key generation is performed.
    """
    key = os.environ.get('FERNET_KEY')
    if not key or not key.strip():
        raise ImproperlyConfigured(
            "FERNET_KEY environment variable is missing. "
            "Generate one using: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
            "and add it to your .env file."
        )

    try:
        return Fernet(key.strip().encode('utf-8'))
    except Exception as exc:
        raise ImproperlyConfigured(
            "FERNET_KEY is invalid. It must be a 32-byte URL-safe base64-encoded key."
        ) from exc


def encrypt_text(plain_text: str) -> str:
    """
    Encrypts a plaintext string into a base64-encoded ciphertext string.

    Flow:
    plain_text (str) -> utf-8 bytes -> Fernet.encrypt() -> base64 token bytes -> str
    """
    if not isinstance(plain_text, str):
        plain_text = str(plain_text)

    fernet = get_fernet()
    encrypted_bytes = fernet.encrypt(plain_text.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')


def decrypt_text(cipher_text: str) -> str:
    """
    Decrypts a base64-encoded ciphertext string back into original plaintext.

    Flow:
    cipher_text (str) -> utf-8 bytes -> Fernet.decrypt() -> plain bytes -> utf-8 str

    Raises DecryptionError if the token is invalid, corrupted, or tampered with.
    """
    if not cipher_text:
        return ""

    fernet = get_fernet()
    try:
        decrypted_bytes = fernet.decrypt(cipher_text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except InvalidToken as exc:
        raise DecryptionError(
            "Failed to decrypt note: ciphertext is invalid, corrupted, or key does not match."
        ) from exc
