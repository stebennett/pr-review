"""Fernet encryption utilities for secure token storage.

This module provides functions for encrypting and decrypting sensitive data
such as GitHub access tokens and Personal Access Tokens (PATs) using Fernet
symmetric encryption.

Example usage:
    >>> from pr_review_shared import encrypt_token, decrypt_token, generate_encryption_key
    >>> key = generate_encryption_key()
    >>> encrypted = encrypt_token("my-secret-token", key)
    >>> decrypted = decrypt_token(encrypted, key)
    >>> assert decrypted == "my-secret-token"
"""

import base64

from cryptography.fernet import Fernet, InvalidToken


class EncryptionError(Exception):
    """Raised when encryption fails."""

    pass


class DecryptionError(Exception):
    """Raised when decryption fails."""

    pass


class InvalidKeyError(Exception):
    """Raised when an invalid encryption key is provided."""

    pass


def generate_encryption_key() -> str:
    """Generate a new valid Fernet encryption key.

    Returns:
        A URL-safe base64-encoded 32-byte key as a string.

    Example:
        >>> key = generate_encryption_key()
        >>> len(base64.urlsafe_b64decode(key))
        32
    """
    return Fernet.generate_key().decode("utf-8")


def _get_fernet(key: str) -> Fernet:
    """Create a Fernet instance from a key string.

    Args:
        key: A URL-safe base64-encoded 32-byte key.

    Returns:
        A Fernet instance configured with the provided key.

    Raises:
        InvalidKeyError: If the key is not a valid Fernet key.
    """
    try:
        return Fernet(key.encode("utf-8"))
    except (ValueError, TypeError) as e:
        raise InvalidKeyError(f"Invalid encryption key: {e}") from e


def encrypt_token(plaintext: str, key: str) -> str:
    """Encrypt a token using Fernet symmetric encryption.

    Args:
        plaintext: The token string to encrypt.
        key: A valid Fernet key (URL-safe base64-encoded 32-byte key).

    Returns:
        The encrypted token as a URL-safe base64-encoded string.

    Raises:
        InvalidKeyError: If the key is not a valid Fernet key.
        EncryptionError: If encryption fails for any other reason.

    Example:
        >>> key = generate_encryption_key()
        >>> encrypted = encrypt_token("ghp_xxxxxxxxxxxx", key)
        >>> isinstance(encrypted, str)
        True
    """
    if not isinstance(plaintext, str):
        raise EncryptionError("Plaintext must be a string")

    if not isinstance(key, str):
        raise InvalidKeyError("Key must be a string")

    try:
        fernet = _get_fernet(key)
        encrypted_bytes = fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")
    except InvalidKeyError:
        raise
    except Exception as e:
        raise EncryptionError(f"Encryption failed: {e}") from e


def decrypt_token(ciphertext: str, key: str) -> str:
    """Decrypt a token using Fernet symmetric encryption.

    Args:
        ciphertext: The encrypted token (URL-safe base64-encoded string).
        key: The same Fernet key used for encryption.

    Returns:
        The decrypted token as a string.

    Raises:
        InvalidKeyError: If the key is not a valid Fernet key.
        DecryptionError: If decryption fails (wrong key, corrupted data, etc.).

    Example:
        >>> key = generate_encryption_key()
        >>> encrypted = encrypt_token("my-secret", key)
        >>> decrypt_token(encrypted, key)
        'my-secret'
    """
    if not isinstance(ciphertext, str):
        raise DecryptionError("Ciphertext must be a string")

    if not isinstance(key, str):
        raise InvalidKeyError("Key must be a string")

    try:
        fernet = _get_fernet(key)
        decrypted_bytes = fernet.decrypt(ciphertext.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidKeyError:
        raise
    except InvalidToken as e:
        raise DecryptionError(
            "Decryption failed: invalid token or wrong key"
        ) from e
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {e}") from e
