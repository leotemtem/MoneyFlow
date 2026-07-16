"""
Input Validation Utilities
Provides validation functions for user inputs
"""

import re


class InputValidator:
    """Validate user inputs with detailed error messages"""

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """
        Validate username according to system rules

        Rules:
        - At least 3 characters
        - No spaces
        - Only letters, numbers, and underscores
        - Cannot start with a number

        Args:
            username: Username to validate

        Returns:
            (is_valid: bool, message: str)
        """
        username = username.strip()

        if not username:
            return False, "Username is required"

        if len(username) < 3:
            return False, "Username must be at least 3 characters long"

        if len(username) > 30:
            return False, "Username cannot exceed 30 characters"

        if " " in username:
            return False, "Username cannot contain spaces. Use underscores (_) instead."

        # Check if username contains only alphanumeric and underscore
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", username):
            if username[0].isdigit():
                return False, "Username cannot start with a number"
            return (
                False,
                "Username can only contain letters, numbers, and underscores (no special characters)",
            )

        return True, "Username is valid"

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password according to security rules

        Rules:
        - At least 6 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains number

        Args:
            password: Password to validate

        Returns:
            (is_valid: bool, message: str)
        """
        if not password:
            return False, "Password is required"

        if len(password) < 6:
            return False, "Password must be at least 6 characters long"

        if len(password) > 128:
            return False, "Password cannot exceed 128 characters"

        # Check password strength
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        missing_requirements = []
        if not has_upper:
            missing_requirements.append("uppercase letter (A-Z)")
        if not has_lower:
            missing_requirements.append("lowercase letter (a-z)")
        if not has_digit:
            missing_requirements.append("number (0-9)")

        if missing_requirements:
            return False, f"Password must contain: {', '.join(missing_requirements)}"

        return True, "Password is strong"

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """
        Validate email format (basic validation)

        Args:
            email: Email to validate

        Returns:
            (is_valid: bool, message: str)
        """
        if not email:
            return True, "Email is optional"  # Email is optional

        # Basic email pattern
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, email):
            return False, "Invalid email format (e.g., user@example.com)"

        if len(email) > 254:  # RFC 5321
            return False, "Email address is too long"

        return True, "Email is valid"

    @staticmethod
    def sanitize_username(username: str) -> str:
        """
        Sanitize username by removing invalid characters

        Args:
            username: Raw username input

        Returns:
            Sanitized username
        """
        # Remove spaces and replace with underscores
        sanitized = username.replace(" ", "_")

        # Remove any character that's not alphanumeric or underscore
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "", sanitized)

        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = "_" + sanitized

        return sanitized

    @staticmethod
    def get_password_strength(password: str) -> str:
        """
        Evaluate password strength

        Args:
            password: Password to evaluate

        Returns:
            Strength level: 'weak', 'medium', 'strong', 'very_strong'
        """
        if not password:
            return "weak"

        score = 0

        # Length
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1

        # Character variety
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1

        # Patterns
        if not re.search(r"(.)\1{2,}", password):  # No repeated characters
            score += 1

        if score <= 2:
            return "weak"
        elif score <= 4:
            return "medium"
        elif score <= 6:
            return "strong"
        else:
            return "very_strong"
