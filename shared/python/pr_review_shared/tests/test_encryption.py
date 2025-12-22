"""Tests for the encryption module."""

import base64

import pytest

from pr_review_shared import decrypt_token, encrypt_token, generate_encryption_key
from pr_review_shared.encryption import DecryptionError, EncryptionError, InvalidKeyError


class TestGenerateEncryptionKey:
    """Tests for generate_encryption_key function."""

    def test_generates_valid_fernet_key(self):
        """Generated key should be a valid Fernet key."""
        key = generate_encryption_key()

        # Should be a string
        assert isinstance(key, str)

        # Should be valid base64
        decoded = base64.urlsafe_b64decode(key)

        # Fernet keys are 32 bytes
        assert len(decoded) == 32

    def test_generates_unique_keys(self):
        """Each call should generate a unique key."""
        keys = [generate_encryption_key() for _ in range(10)]
        assert len(set(keys)) == 10


class TestEncryptToken:
    """Tests for encrypt_token function."""

    def test_encrypts_token_successfully(self):
        """Should encrypt a token and return a string."""
        key = generate_encryption_key()
        plaintext = "ghp_xxxxxxxxxxxxxxxxxxxx"

        encrypted = encrypt_token(plaintext, key)

        assert isinstance(encrypted, str)
        assert encrypted != plaintext

    def test_different_encryptions_produce_different_ciphertext(self):
        """Same plaintext should produce different ciphertext each time."""
        key = generate_encryption_key()
        plaintext = "my-secret-token"

        encrypted1 = encrypt_token(plaintext, key)
        encrypted2 = encrypt_token(plaintext, key)

        # Fernet includes a timestamp, so same plaintext produces different ciphertext
        assert encrypted1 != encrypted2

    def test_raises_invalid_key_error_for_invalid_key(self):
        """Should raise InvalidKeyError for invalid keys."""
        with pytest.raises(InvalidKeyError):
            encrypt_token("test", "invalid-key")

    def test_raises_invalid_key_error_for_short_key(self):
        """Should raise InvalidKeyError for keys that are too short."""
        short_key = base64.urlsafe_b64encode(b"short").decode()
        with pytest.raises(InvalidKeyError):
            encrypt_token("test", short_key)

    def test_raises_invalid_key_error_for_non_string_key(self):
        """Should raise InvalidKeyError when key is not a string."""
        with pytest.raises(InvalidKeyError):
            encrypt_token("test", 12345)

    def test_raises_encryption_error_for_non_string_plaintext(self):
        """Should raise EncryptionError when plaintext is not a string."""
        key = generate_encryption_key()
        with pytest.raises(EncryptionError):
            encrypt_token(12345, key)

    def test_encrypts_empty_string(self):
        """Should handle empty string encryption."""
        key = generate_encryption_key()
        encrypted = encrypt_token("", key)
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

    def test_encrypts_unicode_characters(self):
        """Should handle unicode characters."""
        key = generate_encryption_key()
        plaintext = "token-with-emoji-🔐-and-日本語"

        encrypted = encrypt_token(plaintext, key)
        decrypted = decrypt_token(encrypted, key)

        assert decrypted == plaintext


class TestDecryptToken:
    """Tests for decrypt_token function."""

    def test_decrypts_token_successfully(self):
        """Should decrypt an encrypted token correctly."""
        key = generate_encryption_key()
        original = "ghp_xxxxxxxxxxxxxxxxxxxx"

        encrypted = encrypt_token(original, key)
        decrypted = decrypt_token(encrypted, key)

        assert decrypted == original

    def test_raises_decryption_error_for_wrong_key(self):
        """Should raise DecryptionError when using wrong key."""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        encrypted = encrypt_token("secret", key1)

        with pytest.raises(DecryptionError):
            decrypt_token(encrypted, key2)

    def test_raises_decryption_error_for_corrupted_ciphertext(self):
        """Should raise DecryptionError for corrupted ciphertext."""
        key = generate_encryption_key()

        with pytest.raises(DecryptionError):
            decrypt_token("not-valid-ciphertext", key)

    def test_raises_invalid_key_error_for_invalid_key(self):
        """Should raise InvalidKeyError for invalid keys."""
        with pytest.raises(InvalidKeyError):
            decrypt_token("test", "invalid-key")

    def test_raises_invalid_key_error_for_non_string_key(self):
        """Should raise InvalidKeyError when key is not a string."""
        with pytest.raises(InvalidKeyError):
            decrypt_token("test", 12345)

    def test_raises_decryption_error_for_non_string_ciphertext(self):
        """Should raise DecryptionError when ciphertext is not a string."""
        key = generate_encryption_key()
        with pytest.raises(DecryptionError):
            decrypt_token(12345, key)

    def test_decrypts_empty_string(self):
        """Should handle empty string round-trip."""
        key = generate_encryption_key()
        encrypted = encrypt_token("", key)
        decrypted = decrypt_token(encrypted, key)
        assert decrypted == ""


class TestRoundTrip:
    """Tests for encryption/decryption round-trip."""

    def test_round_trip_with_various_tokens(self):
        """Should correctly round-trip various token formats."""
        key = generate_encryption_key()
        tokens = [
            "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "simple-token",
            "a",
            "x" * 1000,
            "token with spaces",
            "token\nwith\nnewlines",
        ]

        for original in tokens:
            encrypted = encrypt_token(original, key)
            decrypted = decrypt_token(encrypted, key)
            assert decrypted == original, f"Failed for token: {original[:20]}..."

    def test_round_trip_with_same_key_multiple_times(self):
        """Should work with same key for multiple encrypt/decrypt cycles."""
        key = generate_encryption_key()

        for i in range(100):
            original = f"token-{i}"
            encrypted = encrypt_token(original, key)
            decrypted = decrypt_token(encrypted, key)
            assert decrypted == original


class TestModuleExports:
    """Tests for module-level exports."""

    def test_functions_exported_from_package(self):
        """Main functions should be importable from package root."""
        from pr_review_shared import (
            decrypt_token,
            encrypt_token,
            generate_encryption_key,
        )

        assert callable(encrypt_token)
        assert callable(decrypt_token)
        assert callable(generate_encryption_key)

    def test_exceptions_exported_from_encryption_module(self):
        """Exception classes should be importable from encryption module."""
        from pr_review_shared.encryption import (
            DecryptionError,
            EncryptionError,
            InvalidKeyError,
        )

        assert issubclass(EncryptionError, Exception)
        assert issubclass(DecryptionError, Exception)
        assert issubclass(InvalidKeyError, Exception)
