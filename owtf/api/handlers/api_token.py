"""
owtf.api.handlers.auth
~~~~~~~~~~~~~~~~~~~~~~~~

"""
from owtf.api.handlers.base import APIRequestHandler
from owtf.api.handlers.jwtauth import jwtauth
from uuid import uuid4
from owtf.models.api_token import ApiToken
import jwt
secret_key = "my_secret_key"

options = {
    'verify_signature': True,
    'verify_exp': True,
    'verify_nbf': False,
    'verify_iat': True,
    'verify_aud': False
}

@jwtauth
class ApiTokenGenerateHandler(APIRequestHandler):
    """
        doc
    """
    SUPPORTED_METHODS = ["GET"]

    def get(self):
        api_key = str(uuid4())
        token = self.request.headers.get('Authorization').split()[1]
        payload = jwt.decode(
            token,
            secret_key,
            options=options
        )
        user_id = payload['user_id']
        ApiToken.add_api_token(self.session, api_key, user_id)
        data = {
            "status": "ok",
            "api_key": api_key
        }
        return self.success(data)