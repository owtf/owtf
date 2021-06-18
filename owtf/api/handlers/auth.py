"""
owtf.api.handlers.auth
~~~~~~~~~~~~~~~~~~~~~~~~

"""
from owtf.models.user_login_token import UserLoginToken
from owtf.api.handlers.base import APIRequestHandler
from owtf.lib.exceptions import APIError
from owtf.models.user import User
from datetime import datetime, timedelta
import bcrypt
import json
import jwt
import re
from owtf.settings import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_EXP_DELTA_SECONDS,
    is_password_valid_regex,
    is_email_valid_regex,
)
from owtf.db.session import Session


class LogInHandler(APIRequestHandler):
    """LogIn using the correct credentials (email, password). After successfull login a JWT Token is generated"""

    SUPPORTED_METHODS = ["POST"]

    def post(self):
        """
        **Example request**:

        .. sourcecode:: http

        POST /api/v1/login/ HTTP/1.1
        Content-Type: application/json; charset=UTF-8

        {
            "email": "test@test.com",
            "password": "Test@34335",
        }

        **Example response**:

        .. sourcecode:: http

        **Login successful response**;
        HTTP/1.1 200 OK
        Content-Encoding: gzip
        Vary: Accept-Encoding
        Content-Type: application/json; charset=UTF-8

        {
            "status": "success",
            "data": {
                "jwt-token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjozNSwiZXhwIjoxNjIzMjUyMjQwfQ.FjTpJySn3wprlaS26dC9LGBOMrtHJeJsTDJnyCKNmBk"
            }
        }

        **Login failed response**;
        HTTP/1.1 200 OK
        Content-Encoding: gzip
        Vary: Accept-Encoding
        Content-Type: application/json; charset=UTF-8

        {
            "status": "fail",
            "data": "Invalid login credentials"
        }

        """
        body_data = json.loads(self.request.body.decode("utf-8"))
        email = body_data.get("email", None)
        password = body_data.get("password", None)
        if not email:
            raise APIError(400, "Missing email value")
        if not password:
            raise APIError(400, "Missing password value")
        user = User.find_by_email(self.session, email)[0]
        if (
            user
            and user.password
            and bcrypt.hashpw(password.encode("utf-8"), user.password.encode("utf-8")) == user.password.encode("utf-8")
        ):
            payload = {"user_id": user.id, "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)}
            jwt_token = jwt.encode(payload, JWT_SECRET_KEY, JWT_ALGORITHM)
            data = {"jwt-token": jwt_token.decode("utf-8")}
            UserLoginToken.add_user_login_token(self.session, jwt_token, user.id)
            self.success(data)
        else:
            raise APIError(400, "Invalid login credentials")


class RegisterHandler(APIRequestHandler):
    """Registers a new user when he provides email, name, password and confirm password"""

    SUPPORTED_METHODS = ["POST"]

    def post(self):
        """
        **Example request**:

        .. sourcecode:: http

        POST /api/v1/register/ HTTP/1.1
        Content-Type: application/json; charset=UTF-8

        {
            "email": "test@test.com",
            "password": "Test@34335",
            "confirm_password": "Test@34335",
            "name": "test"
        }

        **Example response**:

        .. sourcecode:: http

        **Successful registration response**
        HTTP/1.1 200 OK
        Content-Encoding: gzip
        Vary: Accept-Encoding
        Content-Type: application/json; charset=UTF-8

        {
            "status": "success",
            "data": "User created successfully"
        }

        **Failed registration response**
        HTTP/1.1 200 OK
        Content-Encoding: gzip
        Vary: Accept-Encoding
        Content-Type: application/json; charset=UTF-8

        {
            "status": "fail",
            "data": "Email already exists"
        }

        """
        body_data = json.loads(self.request.body.decode("utf-8"))
        name = body_data.get("name", None)
        email = body_data.get("email", None)
        password = body_data.get("password", None)
        confirm_password = body_data.get("confirm_password", None)

        if not name:
            raise APIError(400, "Missing username value")
        if not email:
            raise APIError(400, "Missing email value")
        if not password:
            raise APIError(400, "Missing password value")
        if not confirm_password:
            raise APIError(400, "Missing confirm password value")

        already_taken = User.find_by_email(self.session, email)
        match_password = re.search(is_password_valid_regex, password)
        match_email = re.search(is_email_valid_regex, email)

        if password != confirm_password:
            raise APIError(400, "Password doesn't match")
        elif not match_email:
            raise APIError(400, "Choose a valid email")
        elif not match_password:
            raise APIError(400, "Choose a strong password")
        elif already_taken:
            raise APIError(400, "Email already exists")
        else:
            hashed_pass = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            user = {}
            user["email"] = email
            user["password"] = hashed_pass
            user["name"] = name
            User.add_user(self.session, user)
            data = "User created successfully"
            self.success(data)


class LogOutHandler(APIRequestHandler):
    """Logs out the current user and clears the cookie"""

    def get(self):
        """
        **Example request**:

        .. sourcecode:: http

        GET /api/v1/logout/ HTTP/1.1

        **Example response**:

        .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Encoding: gzip
        Vary: Accept-Encoding
        Content-Type: application/json; charset=UTF-8

        {
            "status": "success",
            "data": {
                "status": "ok"
            }
        }

        """
        auth = self.request.headers.get("Authorization")
        if auth:
            parts = auth.split()
            token = parts[1]
            session = Session()
            UserLoginToken.delete_user_login_token(session, token)
            data = "Logged out"
            self.success(data)
        else:
            raise APIError(400, "Invalid Token")
