"""Unit tests for password hashing and file encryption (no DB/HTTP)."""
from backend.auth import (
    create_access_token,
    create_refresh_token,
    get_token_payload,
    hash_password,
    verify_password,
)
from services.file_crypto import ENCRYPTED_SUFFIX, decrypt_bytes, encrypt_bytes, is_encrypted_path


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        h = hash_password("secret-pass-1")
        assert h != "secret-pass-1"
        assert h.startswith("$2")  # bcrypt prefix

    def test_verify_roundtrip(self):
        h = hash_password("correct horse battery")
        assert verify_password("correct horse battery", h) is True

    def test_verify_rejects_wrong(self):
        h = hash_password("right-pass")
        assert verify_password("wrong-pass", h) is False

    def test_verify_rejects_garbage_hash(self):
        assert verify_password("x", "not-a-real-hash") is False

    def test_distinct_salts(self):
        assert hash_password("same") != hash_password("same")

    def test_long_password_over_72_bytes(self):
        long_pw = "a" * 200
        h = hash_password(long_pw)
        assert verify_password(long_pw, h) is True


class TestJWT:
    def test_access_token_decodes(self):
        tok = create_access_token({"sub": "u@bel.by"})
        payload = get_token_payload(tok)
        assert payload["sub"] == "u@bel.by"
        assert payload["type"] == "access"
        assert "jti" in payload

    def test_refresh_token_type(self):
        tok = create_refresh_token({"sub": "u@bel.by"})
        assert get_token_payload(tok)["type"] == "refresh"

    def test_tokens_are_unique_via_jti(self):
        a = create_refresh_token({"sub": "u@bel.by"})
        b = create_refresh_token({"sub": "u@bel.by"})
        assert a != b

    def test_invalid_token_returns_none(self):
        assert get_token_payload("garbage.token.here") is None


class TestFileEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        data = b"%PDF-1.4 secret document bytes \x00\x01\x02"
        enc = encrypt_bytes(data)
        assert enc != data
        assert decrypt_bytes(enc) == data

    def test_encrypted_output_differs_each_call(self):
        data = b"same input"
        assert encrypt_bytes(data) != encrypt_bytes(data)  # Fernet uses random IV

    def test_is_encrypted_path(self):
        assert is_encrypted_path(f"file.pdf{ENCRYPTED_SUFFIX}") is True
        assert is_encrypted_path("file.pdf") is False
