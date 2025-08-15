"""
owtf.proxy.interceptors.base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Base interceptor class for proxy request/response modification.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseInterceptor(ABC):
    """Base class for all interceptors."""

    def __init__(self, name: str, enabled: bool = True, priority: int = 100):
        """
        Initialize the interceptor.

        :param name: Name of the interceptor
        :param enabled: Whether the interceptor is enabled
        :param priority: Priority order (lower numbers = higher priority)
        """
        self.name = name
        self.enabled = enabled
        self.priority = priority
        self.config = {}

    def enable(self):
        """Enable the interceptor."""
        self.enabled = True
        logger.info(f"Interceptor '{self.name}' enabled")

    def disable(self):
        """Disable the interceptor."""
        self.enabled = False
        logger.info(f"Interceptor '{self.name}' disabled")

    def is_enabled(self) -> bool:
        """Check if the interceptor is enabled."""
        return self.enabled

    def set_config(self, config: Dict[str, Any]):
        """Set configuration for the interceptor."""
        self.config = config
        logger.debug(f"Configuration set for interceptor '{self.name}': {config}")

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()

    @abstractmethod
    def modify_request(self, request: Any) -> Any:
        """
        Modify the request before forwarding.

        :param request: The request object to modify
        :return: Modified request object
        """
        pass

    @abstractmethod
    def modify_response(self, response: Any) -> Any:
        """
        Modify the response before sending.

        :param response: The response object to modify
        :return: Modified response object
        """
        pass

    def should_intercept_request(self, request: Any) -> bool:
        """
        Check if this interceptor should intercept the request.
        Override this method to implement custom logic.

        :param request: The request object
        :return: True if should intercept, False otherwise
        """
        return self.enabled

    def should_intercept_response(self, response: Any) -> bool:
        """
        Check if this interceptor should intercept the response.
        Override this method to implement custom logic.

        :param response: The response object
        :return: True if should intercept, False otherwise
        """
        return self.enabled

    def __str__(self):
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled}, priority={self.priority})"

    def __repr__(self):
        return self.__str__()
