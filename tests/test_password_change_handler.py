"""
tests.test_password_change_handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for null checks in PasswordChangeHandler.post()
"""

import unittest
from unittest.mock import MagicMock


class TestPasswordChangeHandlerNullChecks(unittest.TestCase):
    def _make_handler(self, password=None, email_or_username=None, otp=None):
        """Helper to create a mocked PasswordChangeHandler with given arguments."""
        from owtf.api.handlers.auth import PasswordChangeHandler

        handler = PasswordChangeHandler.__new__(PasswordChangeHandler)
        handler.session = MagicMock()
        handler.success = MagicMock()

        def get_argument(name, default=None):
            return {
                "password": password,
                "emailOrUsername": email_or_username,
                "otp": otp,
            }.get(name, default)

        handler.get_argument = get_argument
        return handler

    def test_missing_email_or_username_returns_fail(self):
        handler = self._make_handler(password="Test@1234", email_or_username=None, otp="123456")
        handler.post()
        handler.success.assert_called_once_with({"status": "fail", "message": "Missing email or username"})

    def test_missing_otp_returns_fail(self):
        handler = self._make_handler(password="Test@1234", email_or_username="test@test.com", otp=None)
        handler.post()
        handler.success.assert_called_once_with({"status": "fail", "message": "Missing OTP"})

    def test_missing_password_returns_fail(self):
        handler = self._make_handler(password=None, email_or_username="test@test.com", otp="123456")
        handler.post()
        handler.success.assert_called_once_with({"status": "fail", "message": "Missing password value"})

    def test_missing_fields_do_not_hit_db(self):
        handler = self._make_handler(password="Test@1234", email_or_username=None, otp="123456")
        handler.post()
        handler.session.query.assert_not_called()


if __name__ == "__main__":
    unittest.main()
