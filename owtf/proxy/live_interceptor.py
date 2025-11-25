"""
owtf.proxy.live_interceptor
~~~~~~~~~~~~~~~~~~~~~~~~~~

Live interceptor for real-time request modification.
"""

import logging
import time
import uuid
import re
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class InterceptDecision(Enum):
    """Possible decisions for intercepted requests."""

    FORWARD = "forward"
    DROP = "drop"
    MODIFY = "modify"


@dataclass
class InterceptedRequest:
    """Represents an intercepted request waiting for user decision."""

    id: str
    timestamp: float
    method: str
    url: str
    headers: Dict[str, str]
    body: str
    protocol: str
    decision: Optional[InterceptDecision] = None
    modified_headers: Optional[Dict[str, str]] = None
    modified_body: Optional[str] = None
    timeout: float = 30.0  # 30 second timeout


class LiveInterceptor:
    """Manages live request interception with user decision making."""

    def __init__(self):
        self.enabled = False
        self.url_pattern = None
        self.methods = None
        self.pending_requests: Dict[str, InterceptedRequest] = {}
        self.request_queue = []
        self.max_queue_size = 10

    def enable(self, url_pattern: Optional[str] = None, methods: Optional[list] = None):
        """Enable live interception with optional filters."""
        self.enabled = True
        self.url_pattern = url_pattern
        self.methods = [m.upper() for m in methods] if methods else None
        logger.info(f"Live interceptor enabled with pattern: {url_pattern}, methods: {methods}")

    def disable(self):
        """Disable live interception."""
        self.enabled = False
        # Clear pending requests
        self.pending_requests.clear()
        self.request_queue.clear()
        logger.info("Live interceptor disabled")

    def should_intercept(self, method: str, url: str, protocol: str) -> bool:
        """Check if a request should be intercepted."""
        if not self.enabled:
            return False

        # Check method filter
        if self.methods and method.upper() not in self.methods:
            return False

        # Check URL pattern filter
        if self.url_pattern and not re.search(self.url_pattern, url, re.IGNORECASE):
            return False

        # Only intercept HTTP requests for now (no HTTPS)
        if protocol.lower() != "http":
            return False

        return True

    def intercept_request(
        self, method: str, url: str, headers: Dict[str, str], body: str, protocol: str
    ) -> Tuple[str, bool]:
        """
        Intercept a request and return (request_id, should_wait).

        Returns:
            - request_id: Unique ID for the intercepted request
            - should_wait: True if request should wait for user decision
        """
        if not self.should_intercept(method, url, protocol):
            return "", False

        # Check if we already have a pending request
        if self.pending_requests:
            logger.debug("Request intercepted but another is pending, auto-forwarding")
            return "", False

        # Create intercepted request
        request_id = str(uuid.uuid4())
        intercepted_req = InterceptedRequest(
            id=request_id,
            timestamp=time.time(),
            method=method,
            url=url,
            headers=headers.copy(),
            body=body,
            protocol=protocol,
        )

        # Store the request
        self.pending_requests[request_id] = intercepted_req
        self.request_queue.append(request_id)

        # Limit queue size
        if len(self.request_queue) > self.max_queue_size:
            old_id = self.request_queue.pop(0)
            if old_id in self.pending_requests:
                del self.pending_requests[old_id]

        logger.info(f"Request intercepted: {method} {url} (ID: {request_id})")
        return request_id, True

    def get_pending_request(self) -> Optional[Dict[str, Any]]:
        """Get the current pending request for the frontend."""
        if not self.pending_requests:
            return None

        # Get the oldest request
        if self.request_queue:
            request_id = self.request_queue[0]
            if request_id in self.pending_requests:
                req = self.pending_requests[request_id]
                return asdict(req)
        return None

    def make_decision(
        self,
        request_id: str,
        decision: str,
        modified_headers: Optional[Dict[str, str]] = None,
        modified_body: Optional[str] = None,
    ) -> bool:
        """
        Make a decision on an intercepted request.

        Returns:
            True if decision was applied successfully
        """
        if request_id not in self.pending_requests:
            logger.warning(f"Request ID {request_id} not found")
            return False

        req = self.pending_requests[request_id]

        try:
            req.decision = InterceptDecision(decision)
            if decision == "modify":
                req.modified_headers = modified_headers or {}
                req.modified_body = modified_body or ""

            logger.info(f"Decision made for {request_id}: {decision}")
            return True

        except ValueError:
            logger.error(f"Invalid decision: {decision}")
            return False

    def get_decision(self, request_id: str) -> Optional[InterceptDecision]:
        """Get the decision for a request."""
        if request_id in self.pending_requests:
            return self.pending_requests[request_id].decision
        return None

    def cleanup_request(self, request_id: str):
        """Remove a request from tracking."""
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]
            if request_id in self.request_queue:
                self.request_queue.remove(request_id)

    def check_timeouts(self) -> list:
        """Check for timed out requests and return their IDs."""
        current_time = time.time()
        timed_out = []

        for request_id, req in list(self.pending_requests.items()):
            if current_time - req.timestamp > req.timeout:
                timed_out.append(request_id)
                logger.info(f"Request {request_id} timed out, auto-forwarding")

        # Clean up timed out requests
        for request_id in timed_out:
            self.cleanup_request(request_id)

        return timed_out

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the live interceptor."""
        return {
            "enabled": self.enabled,
            "url_pattern": self.url_pattern,
            "methods": self.methods,
            "pending_count": len(self.pending_requests),
            "queue_size": len(self.request_queue),
        }
