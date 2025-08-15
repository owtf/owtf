"""
owtf.proxy.interceptors.body_modifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Body modification interceptor for proxy requests and responses.
"""

import logging
import re
from typing import Any, Dict, Optional, Union
from .base import BaseInterceptor

logger = logging.getLogger(__name__)


class BodyModifier(BaseInterceptor):
    """Interceptor for modifying HTTP request/response bodies."""

    def __init__(
        self,
        search_replace: Optional[Dict[str, str]] = None,
        body_prepend: Optional[str] = None,
        body_append: Optional[str] = None,
        content_type_filters: Optional[list] = None,
        enabled: bool = True,
        priority: int = 60,
    ):
        """
        Initialize the body modifier interceptor.

        :param search_replace: Dictionary of search:replace patterns
        :param body_prepend: Text to prepend to body
        :param body_append: Text to append to body
        :param content_type_filters: List of content types to process
        :param enabled: Whether the interceptor is enabled
        :param priority: Priority order
        """
        super().__init__(f"Body Modifier", enabled, priority)

        self.search_replace = search_replace or {}
        self.body_prepend = body_prepend
        self.body_append = body_append
        self.content_type_filters = content_type_filters or [
            "text/html",
            "text/plain",
            "application/json",
            "application/xml",
        ]

        # Set initial config
        self.config = {
            "search_replace": self.search_replace,
            "body_prepend": self.body_prepend,
            "body_append": self.body_append,
            "content_type_filters": self.content_type_filters,
        }

    def _should_process_content_type(self, content_type: str) -> bool:
        """Check if content type should be processed."""
        if not content_type:
            return False

        for filter_type in self.content_type_filters:
            if filter_type in content_type.lower():
                return True
        return False

    def _get_content_type(self, obj: Any) -> str:
        """Extract content type from request/response object."""
        if hasattr(obj, "headers"):
            return obj.headers.get("Content-Type", "")
        return ""

    def _get_body(self, obj: Any) -> str:
        """Extract body from request/response object."""
        if hasattr(obj, "body"):
            return obj.body or ""
        return ""

    def _set_body(self, obj: Any, body: str):
        """Set body in request/response object."""
        if hasattr(obj, "body"):
            obj.body = body

    def modify_request(self, request: Any) -> Any:
        """
        Modify request body.

        :param request: The request object
        :return: Modified request object
        """
        if not self.should_intercept_request(request):
            return request

        try:
            content_type = self._get_content_type(request)
            if not self._should_process_content_type(content_type):
                return request

            body = self._get_body(request)
            if not body:
                return request

            # Apply search and replace
            modified_body = body
            for search_pattern, replace_text in self.search_replace.items():
                try:
                    modified_body = re.sub(search_pattern, replace_text, modified_body, flags=re.IGNORECASE)
                    logger.debug(f"Applied search/replace '{search_pattern}' -> '{replace_text}' to request body")
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{search_pattern}': {e}")

            # Prepend text
            if self.body_prepend:
                modified_body = self.body_prepend + modified_body
                logger.debug(f"Prepended text to request body")

            # Append text
            if self.body_append:
                modified_body = modified_body + self.body_append
                logger.debug(f"Appended text to request body")

            # Update body if modified
            if modified_body != body:
                self._set_body(request, modified_body)
                logger.info(f"Modified request body (size: {len(body)} -> {len(modified_body)})")

        except Exception as e:
            logger.error(f"Error modifying request body: {e}")

        return request

    def modify_response(self, response: Any) -> Any:
        """
        Modify response body.

        :param response: The response object
        :return: Modified response object
        """
        if not self.should_intercept_response(response):
            return response

        try:
            content_type = self._get_content_type(response)
            if not self._should_process_content_type(content_type):
                return response

            body = self._get_body(response)
            if not body:
                return response

            # Apply search and replace
            modified_body = body
            for search_pattern, replace_text in self.search_replace.items():
                try:
                    modified_body = re.sub(search_pattern, replace_text, modified_body, flags=re.IGNORECASE)
                    logger.debug(f"Applied search/replace '{search_pattern}' -> '{replace_text}' to response body")
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{search_pattern}': {e}")

            # Prepend text
            if self.body_prepend:
                modified_body = self.body_prepend + modified_body
                logger.debug(f"Prepended text to response body")

            # Append text
            if self.body_append:
                modified_body = modified_body + self.body_append
                logger.debug(f"Appended text to response body")

            # Update body if modified
            if modified_body != body:
                self._set_body(response, modified_body)
                logger.info(f"Modified response body (size: {len(body)} -> {len(modified_body)})")

        except Exception as e:
            logger.error(f"Error modifying response body: {e}")

        return response

    def add_search_replace(self, search_pattern: str, replace_text: str):
        """Add a search and replace pattern."""
        self.search_replace[search_pattern] = replace_text
        self.config["search_replace"] = self.search_replace
        logger.info(f"Added search/replace pattern: '{search_pattern}' -> '{replace_text}'")

    def remove_search_replace(self, search_pattern: str):
        """Remove a search and replace pattern."""
        if search_pattern in self.search_replace:
            del self.search_replace[search_pattern]
            self.config["search_replace"] = self.search_replace
            logger.info(f"Removed search/replace pattern: '{search_pattern}'")

    def set_body_prepend(self, text: str):
        """Set text to prepend to body."""
        self.body_prepend = text
        self.config["body_prepend"] = self.body_prepend
        logger.info(f"Set body prepend text: '{text}'")

    def set_body_append(self, text: str):
        """Set text to append to body."""
        self.body_append = text
        self.config["body_append"] = self.body_append
        logger.info(f"Set body append text: '{text}'")
