"""
owtf.proxy.interceptor_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Interceptor manager for coordinating proxy request/response modifications.
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional, Type
from .interceptors import BaseInterceptor, HeaderModifier, BodyModifier, URLRewriter, DelayInjector

logger = logging.getLogger(__name__)


class InterceptorManager:
    """Manages all interceptors and their execution order."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the interceptor manager.

        :param config_file: Optional path to configuration file
        """
        self.request_interceptors: List[BaseInterceptor] = []
        self.response_interceptors: List[BaseInterceptor] = []
        self.interception_rules: List[Dict[str, Any]] = []
        self.config_file = config_file or "/tmp/owtf/interceptor_config.json"

        # Create default interceptors
        self._create_default_interceptors()

        # Load configuration if file exists
        self.load_config()

    def _create_default_interceptors(self):
        """Create and add default interceptors."""
        # Header modifier - high priority for security headers
        header_interceptor = HeaderModifier(
            headers_to_add={"X-OWTF-Proxy": "1.0", "X-Intercepted": "true"}, priority=10
        )
        self.add_interceptor(header_interceptor)

        # URL rewriter - medium priority
        url_interceptor = URLRewriter(priority=40)
        self.add_interceptor(url_interceptor)

        # Body modifier - lower priority
        body_interceptor = BodyModifier(priority=60)
        self.add_interceptor(body_interceptor)

        # Delay injector - lowest priority
        delay_interceptor = DelayInjector(priority=70)
        self.add_interceptor(delay_interceptor)

        logger.info("Created default interceptors")

    def add_interceptor(self, interceptor: BaseInterceptor, position: Optional[int] = None):
        """
        Add an interceptor to the chain.

        :param interceptor: The interceptor to add
        :param position: Position to insert at (None for end)
        """
        if position is None:
            self.request_interceptors.append(interceptor)
        else:
            self.request_interceptors.insert(position, interceptor)

        # Sort by priority
        self.request_interceptors.sort(key=lambda x: x.priority)
        self.response_interceptors.sort(key=lambda x: x.priority)

        logger.info(f"Added interceptor '{interceptor.name}' at priority {interceptor.priority}")

    def remove_interceptor(self, interceptor_id: str):
        """
        Remove an interceptor by ID.

        :param interceptor_id: ID of the interceptor to remove
        """
        # Find by name (using as ID for simplicity)
        for i, interceptor in enumerate(self.request_interceptors):
            if interceptor.name == interceptor_id:
                removed = self.request_interceptors.pop(i)
                logger.info(f"Removed interceptor '{removed.name}'")
                return

        logger.warning(f"Interceptor with ID '{interceptor_id}' not found")

    def get_interceptor(self, interceptor_id: str) -> Optional[BaseInterceptor]:
        """
        Get an interceptor by ID.

        :param interceptor_id: ID of the interceptor
        :return: The interceptor or None if not found
        """
        for interceptor in self.request_interceptors:
            if interceptor.name == interceptor_id:
                return interceptor
        return None

    def get_interceptors(self) -> List[Dict[str, Any]]:
        """
        Get all interceptors as serializable dictionaries.

        :return: List of interceptor configurations
        """
        interceptors = []
        for interceptor in self.request_interceptors:
            interceptors.append(
                {
                    "id": interceptor.name,
                    "name": interceptor.name,
                    "type": "request",
                    "enabled": interceptor.enabled,
                    "priority": interceptor.priority,
                    "config": interceptor.get_config(),
                }
            )
        return interceptors

    def enable_interceptor(self, interceptor_id: str):
        """Enable an interceptor."""
        interceptor = self.get_interceptor(interceptor_id)
        if interceptor:
            interceptor.enable()
            logger.info(f"Enabled interceptor '{interceptor_id}'")
        else:
            logger.warning(f"Interceptor '{interceptor_id}' not found")

    def disable_interceptor(self, interceptor_id: str):
        """Disable an interceptor."""
        interceptor = self.get_interceptor(interceptor_id)
        if interceptor:
            interceptor.disable()
            logger.info(f"Disabled interceptor '{interceptor_id}'")
        else:
            logger.warning(f"Interceptor '{interceptor_id}' not found")

    def update_interceptor_config(self, interceptor_id: str, config: Dict[str, Any]):
        """Update interceptor configuration."""
        interceptor = self.get_interceptor(interceptor_id)
        if interceptor:
            interceptor.set_config(config)
            logger.info(f"Updated config for interceptor '{interceptor_id}'")
        else:
            logger.warning(f"Interceptor '{interceptor_id}' not found")

    def add_rule(self, rule: Dict[str, Any]):
        """
        Add an interception rule.

        :param rule: Rule configuration dictionary
        """
        self.interception_rules.append(rule)
        logger.info(f"Added interception rule: {rule.get('name', 'Unnamed')}")

    def remove_rule(self, rule_id: str):
        """Remove an interception rule."""
        for i, rule in enumerate(self.interception_rules):
            if rule.get("id") == rule_id:
                removed = self.interception_rules.pop(i)
                logger.info(f"Removed rule '{removed.get('name', 'Unnamed')}'")
                return
        logger.warning(f"Rule with ID '{rule_id}' not found")

    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all interception rules."""
        return self.interception_rules.copy()

    def should_intercept(self, request: Any) -> bool:
        """
        Check if request should be intercepted based on rules.

        :param request: The request object
        :return: True if should intercept, False otherwise
        """
        if not self.interception_rules:
            return True

        for rule in self.interception_rules:
            if not rule.get("enabled", True):
                continue

            if self._rule_matches(request, rule):
                return True

        return False

    def _rule_matches(self, request: Any, rule: Dict[str, Any]) -> bool:
        """Check if a rule matches the request."""
        try:
            # URL pattern matching
            if "url_pattern" in rule:
                import re

                url = getattr(request, "url", "") or getattr(request, "uri", "")
                if not re.search(rule["url_pattern"], url, re.IGNORECASE):
                    return False

            # Method matching
            if "methods" in rule:
                method = getattr(request, "method", "").upper()
                if method not in rule["methods"]:
                    return False

            # Content type matching
            if "content_types" in rule:
                content_type = ""
                if hasattr(request, "headers"):
                    content_type = request.headers.get("Content-Type", "")
                if not any(ct in content_type.lower() for ct in rule["content_types"]):
                    return False

        except Exception as e:
            logger.error(f"Error checking rule match: {e}")
            return False

        return True

    def intercept_request(self, request: Any) -> Any:
        """
        Apply all request interceptors.

        :param request: The request object
        :return: Modified request object
        """
        if not self.should_intercept(request):
            return request

        try:
            modified_request = request

            # Apply interceptors in priority order
            for interceptor in self.request_interceptors:
                if interceptor.is_enabled():
                    try:
                        modified_request = interceptor.modify_request(modified_request)
                    except Exception as e:
                        logger.error(f"Error in interceptor '{interceptor.name}': {e}")

            return modified_request

        except Exception as e:
            logger.error(f"Error during request interception: {e}")
            return request

    def intercept_response(self, response: Any) -> Any:
        """
        Apply all response interceptors.

        :param response: The response object
        :return: Modified response object
        """
        try:
            modified_response = response

            # Apply interceptors in priority order
            for interceptor in self.response_interceptors:
                if interceptor.is_enabled():
                    try:
                        modified_response = interceptor.modify_response(modified_response)
                    except Exception as e:
                        logger.error(f"Error in interceptor '{interceptor.name}': {e}")

            return modified_response

        except Exception as e:
            logger.error(f"Error during response interception: {e}")
            return response

    def save_config(self):
        """Save current configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            config = {"interceptors": self.get_interceptors(), "rules": self.get_rules()}

            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)

            logger.info(f"Configuration saved to {self.config_file}")

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def load_config(self):
        """Load configuration from file."""
        try:
            if not os.path.exists(self.config_file):
                logger.info("No configuration file found, using defaults")
                return

            with open(self.config_file, "r") as f:
                config = json.load(f)

            # Load interceptor configurations
            if "interceptors" in config:
                for interceptor_config in config["interceptors"]:
                    interceptor = self.get_interceptor(interceptor_config["id"])
                    if interceptor:
                        interceptor.set_config(interceptor_config.get("config", {}))
                        if not interceptor_config.get("enabled", True):
                            interceptor.disable()

            # Load rules
            if "rules" in config:
                self.interception_rules = config["rules"]

            logger.info(f"Configuration loaded from {self.config_file}")

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the interceptor manager."""
        return {
            "total_interceptors": len(self.request_interceptors),
            "enabled_interceptors": len([i for i in self.request_interceptors if i.is_enabled()]),
            "total_rules": len(self.interception_rules),
            "enabled_rules": len([r for r in self.interception_rules if r.get("enabled", True)]),
            "interception_enabled": True,
        }
