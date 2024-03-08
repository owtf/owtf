"""
owtf.api.handlers.api_token
~~~~~~~~~~~~~~~~~~~~~~~~

"""
from owtf.api.handlers.base import APIRequestHandler
from owtf.api.handlers.jwtauth import jwtauth
from uuid import uuid4
from owtf.models.api_token import ApiToken
import jwt
from owtf.settings import JWT_SECRET_KEY, JWT_OPTIONS, JWT_ALGORITHM
from owtf.lib.exceptions import APIError


@jwtauth
class ApiTokenGenerateHandler(APIRequestHandler):
    """Create the api token for a user."""

    SUPPORTED_METHODS = ["GET"]

    def get(self):
        """Get api token for a logged in user

        **Example request**:

        .. sourcecode:: http

        GET /api/v1/generate/api_token/
        Accept: application/json, text/javascript, */*
        X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

        **ApiToken successful response**;
        HTTP/1.1 200 OK
        Content-Encoding: gzip
        Vary: Accept-Encoding
        Content-Type: application/json

        {
            "status": "success",
            "data": {
                "api_key": "b9e7157c-2150-4e34-b3f1-1777a75debb7"
            }
        }

        """
        api_key = str(uuid4())
        try:
            token = self.request.headers.get("Authorization").split()[1]
            payload = jwt.decode(token, JWT_SECRET_KEY, options=JWT_OPTIONS, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("user_id", None)
            if not user_id:
                raise APIError(400, "Invalid User Id")
            ApiToken.add_api_token(self.session, api_key, user_id)
            data = {"api_key": api_key}
            return self.success(data)
        except Exception:
            raise APIError(400, "Invalid Token")
