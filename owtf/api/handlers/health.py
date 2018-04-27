"""
owtf.api.handlers.health
~~~~~~~~~~~~~~~~~~~~~~~~

"""
from owtf.api.handlers.base import APIRequestHandler

__all__ = ["HealthCheckHandler"]


class HealthCheckHandler(APIRequestHandler):
    """API server health check"""

    SUPPORTED_METHODS = ["GET"]

    def get(self):
        """A debug endpoint to check whether the application is alive.

        **Example request**:

        .. sourcecode:: http

            GET /debug/health HTTP/1.1
            Accept: application/json

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "success",
                "data": {
                    "status": "ok"
                }
            }
        """
        self.success({"status": "ok"})
