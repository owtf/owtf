"""Tests that the login and register handlers stop at the first failed check.

``APIRequestHandler.success()`` writes the response and calls ``finish()``.
A validation error must therefore return right away: going on would reach
the user lookups with missing values, and a second error in the same request
would call ``finish()`` again (Tornado raises RuntimeError).
"""

import json
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import tornado.testing
import tornado.web

# Register user models before importing the auth module (as the jwtauth tests do).
import owtf.models.email_confirmation  # noqa: F401
import owtf.models.user  # noqa: F401
import owtf.models.user_login_token  # noqa: F401
from owtf.api.handlers import auth as auth_module
from owtf.api.handlers import base as base_module


class TestAuthValidation(tornado.testing.AsyncHTTPTestCase):
    def runTest(self):
        pass

    def setUp(self):
        for target, value in (
            (base_module, "get_db_engine"),
            (base_module, "Session"),
        ):
            patcher = patch.object(target, value, MagicMock())
            patcher.start()
            self.addCleanup(patcher.stop)
        self.user = MagicMock()
        self.user.find_by_email.return_value = None
        self.user.find_by_name.return_value = None
        patcher = patch.object(auth_module, "User", self.user)
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()

    def get_app(self):
        return tornado.web.Application(
            [
                (r"/login/", auth_module.LogInHandler),
                (r"/register/", auth_module.RegisterHandler),
            ]
        )

    def post(self, path, **fields):
        response = self.fetch(path, method="POST", body=urlencode(fields))
        self.assertEqual(response.code, 200)
        return json.loads(response.body)

    def assert_fail(self, body, message):
        self.assertEqual(body, {"status": "success", "data": {"status": "fail", "message": message}})

    def test_login_without_any_field_reports_only_the_first(self):
        body = self.post("/login/")
        self.assert_fail(body, "Missing email or username value")
        self.user.find_by_email.assert_not_called()

    def test_login_without_password_does_not_look_up_the_user(self):
        body = self.post("/login/", emailOrUsername="alice")
        self.assert_fail(body, "Missing password value")
        self.user.find_by_email.assert_not_called()
        self.user.find_by_name.assert_not_called()

    def test_login_with_both_fields_still_checks_credentials(self):
        body = self.post("/login/", emailOrUsername="alice", password="x")
        self.assert_fail(body, "Invalid login credentials")
        self.user.find_by_email.assert_called_once()

    def test_register_without_any_field_reports_only_the_first(self):
        body = self.post("/register/")
        self.assert_fail(body, "Missing username value")
        self.user.find_by_email.assert_not_called()
        self.user.add_user.assert_not_called()

    def test_register_stops_at_each_missing_field(self):
        complete = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "Str0ng!Passw0rd",
            "confirm_password": "Str0ng!Passw0rd",
        }
        for missing, message in (
            ("email", "Missing email value"),
            ("password", "Missing password value"),
            ("confirm_password", "Missing confirm password value"),
        ):
            with self.subTest(missing=missing):
                self.user.reset_mock()
                fields = {k: v for k, v in complete.items() if k != missing}
                self.assert_fail(self.post("/register/", **fields), message)
                self.user.find_by_email.assert_not_called()
                self.user.add_user.assert_not_called()
