"""Tests for Argon2 password hashing."""

from moneyflow.auth.passwords import hash_password, needs_rehash, verify_password


def test_hash_is_not_plaintext_and_is_argon2():
    h = hash_password("Secret123")
    assert h != "Secret123"
    assert h.startswith("$argon2")


def test_hash_is_salted_unique_per_call():
    assert hash_password("Secret123") != hash_password("Secret123")


def test_verify_correct_and_incorrect():
    h = hash_password("Secret123")
    assert verify_password(h, "Secret123") is True
    assert verify_password(h, "wrong") is False


def test_verify_handles_empty_and_malformed_without_raising():
    assert verify_password("", "x") is False
    assert verify_password(None, "x") is False
    assert verify_password("not-a-valid-argon2-hash", "x") is False


def test_needs_rehash_false_for_current_params():
    assert needs_rehash(hash_password("Secret123")) is False
