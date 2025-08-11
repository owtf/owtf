"""
owtf.proxy.interceptors.url_rewriter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

URL rewriting interceptor for proxy requests.
"""

import logging
import re
from typing import Any, Dict, Optional, List
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from .base import BaseInterceptor

logger = logging.getLogger(__name__)


class URLRewriter(BaseInterceptor):
    """Interceptor for rewriting URLs in requests."""

    def __init__(
        self,
        url_patterns: Optional[Dict[str, str]] = None,
        query_param_modifications: Optional[Dict[str, str]] = None,
        path_modifications: Optional[Dict[str, str]] = None,
        enabled: bool = True,
        priority: int = 40,
    ):
        """
        Initialize the URL rewriter interceptor.

        :param url_patterns: Dictionary of URL patterns to rewrite
        :param query_param_modifications: Dictionary of query param modifications
        :param path_modifications: Dictionary of path modifications
        :param enabled: Whether the interceptor is enabled
        :param enabled: Whether the interceptor is enabled
        :param priority: Priority order
        """
        super().__init__(f"URL Rewriter", enabled, priority)

        self.url_patterns = url_patterns or {}
        self.query_param_modifications = query_param_modifications or {}
        self.path_modifications = path_modifications or {}

        # Set initial config
        self.config = {
            "url_patterns": self.url_patterns,
            "query_param_modifications": self.query_param_modifications,
            "path_modifications": self.path_modifications,
        }

    def _rewrite_url(self, url: str) -> str:
        """Rewrite URL based on patterns."""
        if not url:
            return url

        modified_url = url

        # Apply URL pattern rewrites
        for pattern, replacement in self.url_patterns.items():
            try:
                modified_url = re.sub(pattern, replacement, modified_url, flags=re.IGNORECASE)
                if modified_url != url:
                    logger.debug(f"Rewrote URL pattern '{pattern}' -> '{replacement}': {url} -> {modified_url}")
                    url = modified_url
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")

        return url

    def _modify_query_params(self, url: str) -> str:
        """Modify query parameters in URL."""
        if not url:
            return url

        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            modified = False

            # Add/remove query parameters
            for param, value in self.query_param_modifications.items():
                if value is None:
                    # Remove parameter
                    if param in query_params:
                        del query_params[param]
                        modified = True
                        logger.debug(f"Removed query parameter '{param}'")
                else:
                    # Add/modify parameter
                    query_params[param] = [value]
                    modified = True
                    logger.debug(f"Set query parameter '{param}' to '{value}'")

            if modified:
                # Reconstruct URL with modified query params
                new_query = urlencode(query_params, doseq=True)
                new_parsed = parsed._replace(query=new_query)
                new_url = urlunparse(new_parsed)
                logger.debug(f"Modified query parameters: {url} -> {new_url}")
                return new_url

        except Exception as e:
            logger.error(f"Error modifying query parameters: {e}")

        return url

    def _modify_path(self, url: str) -> str:
        """Modify URL path."""
        if not url:
            return url

        try:
            parsed = urlparse(url)
            path = parsed.path

            modified = False

            # Apply path modifications
            for pattern, replacement in self.path_modifications.items():
                try:
                    new_path = re.sub(pattern, replacement, path, flags=re.IGNORECASE)
                    if new_path != path:
                        path = new_path
                        modified = True
                        logger.debug(f"Modified path '{pattern}' -> '{replacement}': {parsed.path} -> {path}")
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")

            if modified:
                # Reconstruct URL with modified path
                new_parsed = parsed._replace(path=path)
                new_url = urlunparse(new_parsed)
                logger.debug(f"Modified path: {url} -> {new_url}")
                return new_url

        except Exception as e:
            logger.error(f"Error modifying path: {e}")

        return url

    def modify_request(self, request: Any) -> Any:
        """
        Modify request URL.

        :param request: The request object
        :return: Modified request object
        """
        if not self.should_intercept_request(request):
            return request

        try:
            # Get URL from request
            if hasattr(request, "url"):
                original_url = request.url
            elif hasattr(request, "uri"):
                original_url = request.uri
            else:
                return request

            if not original_url:
                return request

            # Apply URL modifications
            modified_url = original_url

            # Rewrite URL patterns
            modified_url = self._rewrite_url(modified_url)

            # Modify query parameters
            modified_url = self._modify_query_params(modified_url)

            # Modify path
            modified_url = self._modify_path(modified_url)

            # Update request URL if modified
            if modified_url != original_url:
                if hasattr(request, "url"):
                    request.url = modified_url
                if hasattr(request, "uri"):
                    request.uri = modified_url

                logger.info(f"Rewrote request URL: {original_url} -> {modified_url}")

        except Exception as e:
            logger.error(f"Error modifying request URL: {e}")

        return request

    def modify_response(self, response: Any) -> Any:
        """
        Modify response (URLs in response body).

        :param response: The response object
        :return: Modified response object
        """
        if not self.should_intercept_response(response):
            return response

        try:
            # Check if response has body and content type
            if not hasattr(response, "body") or not response.body:
                return response

            content_type = ""
            if hasattr(response, "headers"):
                content_type = response.headers.get("Content-Type", "")

            # Only process HTML and text content for URL rewriting
            if not any(ct in content_type.lower() for ct in ["text/html", "text/plain"]):
                return response

            body = response.body
            modified_body = body

            # Rewrite URLs in response body
            for pattern, replacement in self.url_patterns.items():
                try:
                    modified_body = re.sub(pattern, replacement, modified_body, flags=re.IGNORECASE)
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}' for body modification: {e}")

            # Update response body if modified
            if modified_body != body:
                response.body = modified_body
                logger.info(f"Rewrote URLs in response body (size: {len(body)} -> {len(modified_body)})")

        except Exception as e:
            logger.error(f"Error modifying response URLs: {e}")

        return response

    def add_url_pattern(self, pattern: str, replacement: str):
        """Add a URL pattern rewrite rule."""
        self.url_patterns[pattern] = replacement
        self.config["url_patterns"] = self.url_patterns
        logger.info(f"Added URL pattern: '{pattern}' -> '{replacement}'")

    def remove_url_pattern(self, pattern: str):
        """Remove a URL pattern rewrite rule."""
        if pattern in self.url_patterns:
            del self.url_patterns[pattern]
            self.config["url_patterns"] = self.url_patterns
            logger.info(f"Removed URL pattern: '{pattern}'")

    def add_query_param_modification(self, param: str, value: str):
        """Add a query parameter modification."""
        self.query_param_modifications[param] = value
        self.config["query_param_modifications"] = self.query_param_modifications
        logger.info(f"Added query param modification: '{param}' = '{value}'")

    def remove_query_param(self, param: str):
        """Remove a query parameter."""
        self.query_param_modifications[param] = None
        self.config["query_param_modifications"] = self.query_param_modifications
        logger.info(f"Added query param removal: '{param}'")

    def add_path_modification(self, pattern: str, replacement: str):
        """Add a path modification rule."""
        self.path_modifications[pattern] = replacement
        self.config["path_modifications"] = self.path_modifications
        logger.info(f"Added path modification: '{pattern}' -> '{replacement}'")
