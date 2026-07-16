"""
User Authentication Handler
Manages user registration, login, and session management
"""

from moneyflow.auth.passwords import hash_password
from moneyflow.auth.validators import InputValidator
from moneyflow.database.handler import DatabaseHandler


class AuthHandler:
    """Handle user authentication and registration"""

    def __init__(self):
        """Initialize auth handler with database"""
        self.db = DatabaseHandler()

    def register_user(
        self, username: str, password: str, email: str = "", employment_status: str = ""
    ) -> tuple[bool, str]:
        """
        Register a new user

        Args:
            username: Username
            password: Plain text password
            email: Optional email address
            employment_status: Employment status

        Returns:
            (success: bool, message: str)
        """
        username = username.strip()

        # Validate username
        username_valid, username_msg = InputValidator.validate_username(username)
        if not username_valid:
            return False, username_msg

        # Validate password
        password_valid, password_msg = InputValidator.validate_password(password)
        if not password_valid:
            return False, password_msg

        # Validate email if provided
        if email:
            email_valid, email_msg = InputValidator.validate_email(email)
            if not email_valid:
                return False, email_msg

        # Register in database
        return self.db.register_user(username, password, email, employment_status)

    def authenticate_user(self, username: str, password: str) -> tuple[bool, str]:
        """
        Authenticate a user

        Args:
            username: Username
            password: Plain text password

        Returns:
            (success: bool, message: str)
        """
        if not username or not password:
            return False, "Username and password required"

        return self.db.authenticate_user(username, password)

    def get_user_info(self, username: str) -> dict:
        """Get user information"""
        return self.db.get_user_info(username)

    def change_password(
        self, username: str, old_password: str, new_password: str
    ) -> tuple[bool, str]:
        """
        Change user password

        Args:
            username: Username
            old_password: Current password
            new_password: New password

        Returns:
            (success: bool, message: str)
        """
        # Verify old password first
        success, message = self.authenticate_user(username, old_password)
        if not success:
            return False, "Current password is incorrect"

        # Validate new password
        password_valid, password_msg = InputValidator.validate_password(new_password)
        if not password_valid:
            return False, password_msg

        # Ensure new password is different from old
        if old_password == new_password:
            return False, "New password must be different from current password"

        # Update password in database
        return self.db.change_password(username, hash_password(new_password))

    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        return self.db.user_exists(username)
