"""
owtf.proxy.interceptors.delay_injector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Delay injection interceptor for proxy requests and responses.
"""

import logging
import time
import random
from typing import Any, Dict, Optional, Union
from .base import BaseInterceptor

logger = logging.getLogger(__name__)


class DelayInjector(BaseInterceptor):
    """Interceptor for injecting delays in requests and responses."""

    def __init__(
        self,
        request_delay: Optional[Union[float, tuple]] = None,
        response_delay: Optional[Union[float, tuple]] = None,
        jitter: bool = False,
        delay_conditions: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        priority: int = 70,
    ):
        """
        Initialize the delay injector interceptor.

        :param request_delay: Delay for requests (float or tuple for min/max range)
        :param response_delay: Delay for responses (float or tuple for min/max range)
        :param jitter: Whether to add random jitter to delays
        :param delay_conditions: Conditions for when to apply delays
        :param enabled: Whether the interceptor is enabled
        :param priority: Priority order
        """
        super().__init__(f"Delay Injector", enabled, priority)

        self.request_delay = request_delay
        self.response_delay = response_delay
        self.jitter = jitter
        self.delay_conditions = delay_conditions or {}

        # Set initial config
        self.config = {
            "request_delay": self.request_delay,
            "response_delay": self.response_delay,
            "jitter": self.jitter,
            "delay_conditions": self.delay_conditions,
        }

    def _calculate_delay(self, base_delay: Union[float, tuple]) -> float:
        """Calculate the actual delay to apply."""
        if base_delay is None:
            return 0.0

        if isinstance(base_delay, (list, tuple)) and len(base_delay) == 2:
            # Range: (min, max)
            min_delay, max_delay = base_delay
            delay = random.uniform(min_delay, max_delay)
        else:
            # Fixed delay
            delay = float(base_delay)

        if self.jitter:
            # Add ±10% jitter
            jitter_factor = random.uniform(0.9, 1.1)
            delay *= jitter_factor

        return max(0.0, delay)  # Ensure non-negative

    def _should_delay(self, obj: Any, delay_type: str) -> bool:
        """Check if delay should be applied based on conditions."""
        if not self.delay_conditions:
            return True

        try:
            # Check URL patterns
            if "url_patterns" in self.delay_conditions:
                url = getattr(obj, "url", "") or getattr(obj, "uri", "")
                if url:
                    import re

                    patterns = self.delay_conditions["url_patterns"]
                    for pattern in patterns:
                        if re.search(pattern, url, re.IGNORECASE):
                            return True
                    return False

            # Check HTTP methods
            if "methods" in self.delay_conditions:
                method = getattr(obj, "method", "").upper()
                if method and method not in self.delay_conditions["methods"]:
                    return False

            # Check content types
            if "content_types" in self.delay_conditions:
                content_type = ""
                if hasattr(obj, "headers"):
                    content_type = obj.headers.get("Content-Type", "")
                if content_type:
                    allowed_types = self.delay_conditions["content_types"]
                    if not any(ct in content_type.lower() for ct in allowed_types):
                        return False

            # Check size conditions
            if "min_size" in self.delay_conditions:
                body_size = len(getattr(obj, "body", "") or "")
                if body_size < self.delay_conditions["min_size"]:
                    return False

            if "max_size" in self.delay_conditions:
                body_size = len(getattr(obj, "body", "") or "")
                if body_size > self.delay_conditions["max_size"]:
                    return False

        except Exception as e:
            logger.error(f"Error checking delay conditions: {e}")

        return True

    def modify_request(self, request: Any) -> Any:
        """
        Add delay to request processing.

        :param request: The request object
        :return: Modified request object
        """
        if not self.should_intercept_request(request):
            return request

        if not self._should_delay(request, "request"):
            return request

        delay = self._calculate_delay(self.request_delay)
        if delay > 0:
            logger.debug(
                f"Adding {delay:.2f}s delay to request: {getattr(request, 'url', '') or getattr(request, 'uri', '')}"
            )
            time.sleep(delay)

        return request

    def modify_response(self, response: Any) -> Any:
        """
        Add delay to response processing.

        :param response: The response object
        :return: Modified response object
        """
        if not self.should_intercept_response(response):
            return response

        if not self._should_delay(response, "response"):
            return response

        delay = self._calculate_delay(self.response_delay)
        if delay > 0:
            logger.debug(f"Adding {delay:.2f}s delay to response")
            time.sleep(delay)

        return response

    def set_request_delay(self, delay: Union[float, tuple]):
        """Set the delay for requests."""
        self.request_delay = delay
        self.config["request_delay"] = self.request_delay
        logger.info(f"Set request delay to: {delay}")

    def set_response_delay(self, delay: Union[float, tuple]):
        """Set the delay for responses."""
        self.response_delay = delay
        self.config["response_delay"] = self.response_delay
        logger.info(f"Set response delay to: {delay}")

    def set_jitter(self, enabled: bool):
        """Enable or disable jitter."""
        self.jitter = enabled
        self.config["jitter"] = self.jitter
        logger.info(f"{'Enabled' if enabled else 'Disabled'} delay jitter")

    def add_url_condition(self, pattern: str):
        """Add a URL pattern condition for delays."""
        if "url_patterns" not in self.delay_conditions:
            self.delay_conditions["url_patterns"] = []
        self.delay_conditions["url_patterns"].append(pattern)
        self.config["delay_conditions"] = self.delay_conditions
        logger.info(f"Added URL condition pattern: '{pattern}'")

    def set_method_conditions(self, methods: list):
        """Set HTTP methods that should be delayed."""
        self.delay_conditions["methods"] = [m.upper() for m in methods]
        self.config["delay_conditions"] = self.delay_conditions
        logger.info(f"Set method conditions: {methods}")

    def set_content_type_conditions(self, content_types: list):
        """Set content types that should be delayed."""
        self.delay_conditions["content_types"] = content_types
        self.config["delay_conditions"] = self.delay_conditions
        logger.info(f"Set content type conditions: {content_types}")

    def set_size_conditions(self, min_size: Optional[int] = None, max_size: Optional[int] = None):
        """Set size conditions for delays."""
        if min_size is not None:
            self.delay_conditions["min_size"] = min_size
        if max_size is not None:
            self.delay_conditions["max_size"] = max_size
        self.config["delay_conditions"] = self.delay_conditions
        logger.info(f"Set size conditions: min={min_size}, max={max_size}")
