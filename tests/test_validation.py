"""
Unit tests for InputValidator
"""

import pytest

from moneyflow.auth.validators import InputValidator


class TestUsernameValidation:
    @pytest.mark.parametrize(
        "username, expected",
        [
            ("john_doe", True),
            ("sarah123", True),
            ("alex_smith_99", True),
            ("_validuser", True),
            ("ab", False),  # too short
            ("john doe", False),  # space
            ("123john", False),  # starts with digit
            ("john@doe", False),  # special char @
            ("user!", False),  # special char !
            ("x" * 31, False),  # too long
            ("", False),  # empty
        ],
    )
    def test_username(self, username, expected):
        is_valid, _ = InputValidator.validate_username(username)
        assert is_valid == expected

    def test_error_message_too_short(self):
        _, msg = InputValidator.validate_username("ab")
        assert "3" in msg or "short" in msg.lower() or "characters" in msg.lower()

    def test_error_message_space(self):
        _, msg = InputValidator.validate_username("bad user")
        assert "space" in msg.lower() or "underscore" in msg.lower()


class TestPasswordValidation:
    @pytest.mark.parametrize(
        "password, expected",
        [
            ("MyPass123", True),
            ("SecureP@ss1", True),
            ("MySecurePassword123", True),
            ("Abc123", True),  # minimum valid
            ("abc", False),  # too short
            ("mypass123", False),  # no uppercase
            ("MYPASS123", False),  # no lowercase
            ("MyPassword", False),  # no digit
            ("Pass1", False),  # 5 chars → too short
            ("a" * 129, False),  # too long
            ("", False),  # empty
        ],
    )
    def test_password(self, password, expected):
        is_valid, _ = InputValidator.validate_password(password)
        assert is_valid == expected

    def test_error_message_missing_uppercase(self):
        _, msg = InputValidator.validate_password("mypass123")
        assert "uppercase" in msg.lower() or "A-Z" in msg

    def test_error_message_missing_digit(self):
        _, msg = InputValidator.validate_password("MyPassword")
        assert "number" in msg.lower() or "0-9" in msg


class TestEmailValidation:
    @pytest.mark.parametrize(
        "email, expected",
        [
            ("user@example.com", True),
            ("user.name@domain.co", True),
            ("notanemail", False),
            ("@nodomain", False),
            ("missing@.com", False),
        ],
    )
    def test_email(self, email, expected):
        is_valid, _ = InputValidator.validate_email(email)
        assert is_valid == expected
