"""
owtf.proxy.interceptors.header_modifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Header modification interceptor for proxy requests and responses.
"""

import logging
from typing import Any, Dict, List, Optional
from .base import BaseInterceptor

logger = logging.getLogger(__name__)


class HeaderModifier(BaseInterceptor):
    """Interceptor for modifying HTTP headers."""

    def __init__(
        self,
        headers_to_add: Optional[Dict[str, str]] = None,
        headers_to_remove: Optional[List[str]] = None,
        headers_to_modify: Optional[Dict[str, str]] = None,
        enabled: bool = True,
        priority: int = 50,
    ):
        """
        Initialize the header modifier interceptor.

        :param headers_to_add: Headers to add to requests/responses
        :param headers_to_remove: Headers to remove from requests/responses
        :param headers_to_modify: Headers to modify (key: new_value)
        :param enabled: Whether the interceptor is enabled
        :param priority: Priority order
        """
        super().__init__(f"Header Modifier", enabled, priority)

        self.headers_to_add = headers_to_add or {}
        self.headers_to_remove = headers_to_remove or []
        self.headers_to_modify = headers_to_modify or {}

        # Set initial config
        self.config = {
            "headers_to_add": self.headers_to_add,
            "headers_to_remove": self.headers_to_remove,
            "headers_to_modify": self.headers_to_modify,
        }

    def modify_request(self, request: Any) -> Any:
        """
        Modify request headers.

        :param request: The request object
        :return: Modified request object
        """
        if not self.should_intercept_request(request):
            return request

        try:
            # Remove headers
            for header in self.headers_to_remove:
                if hasattr(request, "headers") and header in request.headers:
                    del request.headers[header]
                    logger.debug(f"Removed header '{header}' from request")

            # Modify existing headers
            for header, new_value in self.headers_to_modify.items():
                if hasattr(request, "headers") and header in request.headers:
                    request.headers[header] = new_value
                    logger.debug(f"Modified header '{header}' to '{new_value}' in request")

            # Add new headers
            for header, value in self.headers_to_add.items():
                if hasattr(request, "headers"):
                    request.headers[header] = value
                    logger.debug(f"Added header '{header}: {value}' to request")

        except Exception as e:
            logger.error(f"Error modifying request headers: {e}")

        return request

    def modify_response(self, response: Any) -> Any:
        """
        Modify response headers.

        :param response: The response object
        :return: Modified response object
        """
        if not self.should_intercept_response(response):
            return response

        try:
            # Remove headers
            for header in self.headers_to_remove:
                if hasattr(response, "headers") and header in response.headers:
                    del response.headers[header]
                    logger.debug(f"Removed header '{header}' from response")

            # Modify existing headers
            for header, new_value in self.headers_to_modify.items():
                if hasattr(response, "headers") and header in response.headers:
                    response.headers[header] = new_value
                    logger.debug(f"Modified header '{header}' to '{new_value}' in response")

            # Add new headers
            for header, value in self.headers_to_add.items():
                if hasattr(response, "headers"):
                    response.headers[header] = value
                    logger.debug(f"Added header '{header}: {value}' to response")

        except Exception as e:
            logger.error(f"Error modifying response headers: {e}")

        return response

    def add_header(self, header: str, value: str):
        """Add a header to be included in requests/responses."""
        self.headers_to_add[header] = value
        self.config["headers_to_add"] = self.headers_to_add
        logger.info(f"Added header '{header}: {value}' to interceptor")

    def remove_header(self, header: str):
        """Remove a header from requests/responses."""
        if header in self.headers_to_remove:
            self.headers_to_remove.remove(header)
        self.headers_to_remove.append(header)
        self.config["headers_to_remove"] = self.headers_to_remove
        logger.info(f"Added header '{header}' to removal list")

    def modify_header(self, header: str, new_value: str):
        """Modify an existing header value."""
        self.headers_to_modify[header] = new_value
        self.config["headers_to_modify"] = self.headers_to_modify
        logger.info(f"Added header modification '{header}: {new_value}' to interceptor")
