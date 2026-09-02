"""
owtf.utils.structured_logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Structured logging for GSoC 2026 components.
Format: COMPONENT|timestamp|event_type|target_id|details

Makes logs parseable for metrics and reporting.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def log_structured(component, event_type, target_id=None, plugin_code=None, details=None):
    """Log a structured event.

    Format: STRUCTURED|timestamp|component|event_type|target_id|plugin_code|details

    :param component: Component name (scheduler, harness, normalizer, etc.)
    :param event_type: Event type (priority_assigned, timeout, duplicate_detected, etc.)
    :param target_id: Target ID (optional)
    :param plugin_code: Plugin code (optional)
    :param details: Additional details as string (optional)
    """
    timestamp = datetime.now().isoformat()
    target = target_id or "N/A"
    plugin = plugin_code or "N/A"
    detail = details or ""

    log_line = f"STRUCTURED|{timestamp}|{component}|{event_type}|{target}|{plugin}|{detail}"
    logger.info(log_line)
