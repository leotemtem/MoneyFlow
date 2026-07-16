"""
Unit tests for AuthHandler
Uses an isolated temporary SQLite database (via the tmp_db / auth_handler fixtures).
"""


class TestRegistration:
    def test_register_new_user(self, auth_handler):
        ok, msg = auth_handler.register_user("alice", "Password1", "alice@example.com")
        assert ok, msg

    def test_register_trims_username_before_persisting(self, auth_handler):
        ok, msg = auth_handler.register_user("  alice_trimmed  ", "Password1")

        assert ok, msg
        assert auth_handler.user_exists("alice_trimmed")
        assert not auth_handler.user_exists("  alice_trimmed  ")

    def test_register_duplicate_user(self, auth_handler):
        auth_handler.register_user("bob", "Password1")
        ok, msg = auth_handler.register_user("bob", "Password1")
        assert not ok
        assert "exists" in msg.lower() or "username" in msg.lower()

    def test_register_short_username(self, auth_handler):
        ok, msg = auth_handler.register_user("ab", "Password1")
        assert not ok

    def test_register_username_with_space(self, auth_handler):
        ok, msg = auth_handler.register_user("bad user", "Password1")
        assert not ok

    def test_register_username_starts_with_number(self, auth_handler):
        ok, msg = auth_handler.register_user("1user", "Password1")
        assert not ok

    def test_register_weak_password_no_upper(self, auth_handler):
        ok, msg = auth_handler.register_user("carol", "password1")
        assert not ok

    def test_register_weak_password_no_digit(self, auth_handler):
        ok, msg = auth_handler.register_user("carol", "Password")
        assert not ok

    def test_register_weak_password_too_short(self, auth_handler):
        ok, msg = auth_handler.register_user("carol", "Ab1")
        assert not ok

    def test_register_valid_email(self, auth_handler):
        ok, msg = auth_handler.register_user("dave", "Password1", "dave@test.com")
        assert ok

    def test_register_invalid_email(self, auth_handler):
        ok, msg = auth_handler.register_user("eve", "Password1", "not-an-email")
        assert not ok


class TestAuthentication:
    def test_login_correct_credentials(self, auth_handler):
        auth_handler.register_user("frank", "Secure99")
        ok, msg = auth_handler.authenticate_user("frank", "Secure99")
        assert ok

    def test_login_wrong_password(self, auth_handler):
        auth_handler.register_user("grace", "Secure99")
        ok, msg = auth_handler.authenticate_user("grace", "WrongPass1")
        assert not ok

    def test_login_nonexistent_user(self, auth_handler):
        ok, msg = auth_handler.authenticate_user("nobody", "Password1")
        assert not ok

    def test_login_empty_credentials(self, auth_handler):
        ok, msg = auth_handler.authenticate_user("", "")
        assert not ok


class TestPasswordChange:
    def test_change_password_success(self, auth_handler):
        auth_handler.register_user("henry", "OldPass1")
        ok, msg = auth_handler.change_password("henry", "OldPass1", "NewPass2")
        assert ok

    def test_new_password_works_after_change(self, auth_handler):
        auth_handler.register_user("iris", "OldPass1")
        auth_handler.change_password("iris", "OldPass1", "NewPass2")
        ok, _ = auth_handler.authenticate_user("iris", "NewPass2")
        assert ok

    def test_old_password_rejected_after_change(self, auth_handler):
        auth_handler.register_user("jack", "OldPass1")
        auth_handler.change_password("jack", "OldPass1", "NewPass2")
        ok, _ = auth_handler.authenticate_user("jack", "OldPass1")
        assert not ok

    def test_change_password_wrong_current(self, auth_handler):
        auth_handler.register_user("karen", "OldPass1")
        ok, msg = auth_handler.change_password("karen", "WrongOld1", "NewPass2")
        assert not ok

    def test_change_password_same_as_old(self, auth_handler):
        auth_handler.register_user("leo", "SamePass1")
        ok, msg = auth_handler.change_password("leo", "SamePass1", "SamePass1")
        assert not ok

    def test_change_password_weak_new(self, auth_handler):
        auth_handler.register_user("mia", "OldPass1")
        ok, msg = auth_handler.change_password("mia", "OldPass1", "weak")
        assert not ok


class TestGetUserInfo:
    def test_user_info_contains_expected_fields(self, auth_handler):
        auth_handler.register_user("nina", "Password1", "nina@example.com")
        info = auth_handler.get_user_info("nina")
        assert "username" in info
        assert "email" in info
        assert "created_at" in info

    def test_user_info_no_password_hash(self, auth_handler):
        auth_handler.register_user("oliver", "Password1")
        info = auth_handler.get_user_info("oliver")
        assert "password_hash" not in info

    def test_user_info_nonexistent_returns_empty(self, auth_handler):
        info = auth_handler.get_user_info("ghost")
        assert info == {}
