"""
owtf.api.handlers.auth
~~~~~~~~~~~~~~~~~~~~~~~~

"""
from owtf.api.handlers.base import APIRequestHandler
from owtf.lib.exceptions import APIError
from owtf.models.user import User
from datetime import datetime, timedelta
import tornado
import bcrypt
import json
import base64
import uuid
import jwt
import re

JWT_SECRET = 'my_secret_key'
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 60 * 60 * 24


class LogInHandler(APIRequestHandler):
    """LogIn using the correct credentials (email, password). After successfull login a JWT Token is generated"""

    SUPPORTED_METHODS = ["POST"]

    def post(self):
        """
            **Example request**:

            .. sourcecode:: http

            POST /api/v1/login/ HTTP/1.1

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
                    "status": "ok",
                    "jwt-token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxOCwiZXhwIjoxNjE1NjU0OTk1fQ.wSMr5laDNVTxuTTJI4FWssnZa2xYL4PS8llDLDB4eyY"
                }
            }

            **Login failed response**;
            HTTP/1.1 200 OK
            Content-Encoding: gzip
            Vary: Accept-Encoding
            Content-Type: application/json; charset=UTF-8

            {
                "status": "success",
                "data": {
                    "status": "fail",
                    "message": "Invalid login credentials"
                }
            }

        """
        body_data = json.loads(self.request.body.decode('utf-8'))
        email = body_data['email']
        password = body_data['password']
        user = User.find_by_email(self.session, email)[0]

        if user and user.password and bcrypt.hashpw(password.encode('utf-8'), user.password.encode('utf-8')) == user.password.encode('utf-8'):
            self.set_current_user(email)
            payload = {
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
            }
            jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
            data = {
                "status": "ok",
                "jwt-token": jwt_token.decode('utf-8')
            }
            self.success(data)

        else:
            error_msg = "Invalid login credentials"
            data = {
                "status": "fail",
                "message": error_msg
            }
            self.success(data)

    def set_current_user(self, user):
        """
            Set user cookie for the logged-in user
            Setting HttpOnly attribute for preventing XSS attacks
            Setting SameSite for preventing CSRF Attacks    
        """

        self.application.settings['cookie_secret'] = base64.b64encode(
            uuid.uuid4().bytes + uuid.uuid4().bytes).decode('utf-8')
        if user:
            self.set_secure_cookie("user", tornado.escape.json_encode(user), secure=True, HttpOnly=True, SameSite='Lax')
        else:
            self.clear_cookie("user")


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
                "data": {
                    "status": "ok"
                }
            }

            **Failed registration response**
            HTTP/1.1 200 OK
            Content-Encoding: gzip
            Vary: Accept-Encoding
            Content-Type: application/json; charset=UTF-8

            {
                "status": "success",
                "data": {
                    "status": "fail",
                    "message": "Email already exists"
                }
            }

        """
        body_data = json.loads(self.request.body.decode('utf-8'))
        name = body_data['name']
        email = body_data['email']
        password = body_data['password']
        confirm_password = body_data['confirm_password']

        already_taken = User.find_by_email(self.session, email)
        reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$"
        pat = re.compile(reg)
        mat = re.search(pat, password)
        data = {
            "status": "fail",
        }
        if password != confirm_password:
            data["message"] = "Password doesn't match"
            self.success(data)
        elif not mat:
            data["message"] = "Choose a strong password"
            self.success(data)
        elif already_taken:
            data["message"] = "Email already exists"
            self.success(data)
        else:
            hashed_pass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(8))
            user = {}
            user['email'] = email
            user['password'] = hashed_pass
            user['name'] = name
            User.add_user(self.session, user)
            data = {
                "status": "ok",
            }
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
        self.clear_cookie("user")
        data = {
            "status": "ok",
        }
        self.success(data)
