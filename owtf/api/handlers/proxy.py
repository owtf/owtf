"""
owtf.api.handlers.proxy
~~~~~~~~~~~~~~~~~~~~~~

API handlers for proxy requests and responses.
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from owtf.api.handlers.base import APIRequestHandler
from owtf.proxy.proxy import REQUEST_LOG_FILE
import json
import time
from datetime import datetime
from urllib.parse import urlparse
from tornado.web import HTTPError

logger = logging.getLogger(__name__)

# --- Refactored log reading and parsing logic ---
def read_proxy_log() -> List[Dict[str, Any]]:
    """Read and parse the proxy log file."""
    entries = []
    if not os.path.exists(REQUEST_LOG_FILE):
        return entries
    try:
        with open(REQUEST_LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        # Split by the separator line
        log_blocks = content.split("-" * 80)
        for block in log_blocks:
            if not block.strip():
                continue
            entry = parse_log_block(block.strip())
            if entry:
                entries.append(entry)
        # Sort by timestamp (newest first)
        entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    except Exception as e:
        logger.error(f"Error reading proxy log: {e}")
    return entries


def parse_log_block(block: str) -> Optional[Dict[str, Any]]:
    """Parse a single log block into a structured entry."""
    try:
        lines = block.split("\n")
        if not lines:
            return None
        # Parse the first line which contains timestamp, protocol, direction, method, url
        first_line = lines[0].strip()
        if not first_line.startswith("["):
            return None
        # Extract timestamp
        timestamp_match = re.match(r"\[([^\]]+)\]", first_line)
        if not timestamp_match:
            return None
        timestamp = timestamp_match.group(1)
        # Parse the rest of the first line
        parts = first_line.split("] ")[1].split(" ")
        if len(parts) < 4:
            return None
        protocol = parts[0]
        direction = parts[1]
        method = parts[2]
        url = " ".join(parts[3:])
        entry = {
            "timestamp": timestamp,
            "protocol": protocol,
            "direction": direction,
            "method": method,
            "url": url,
            "headers": {},
            "body": None,
            "body_size": 0,
        }
        # Parse headers and body from remaining lines
        in_headers = False
        in_body = False
        body_lines = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            if line.startswith("Headers:"):
                in_headers = True
                in_body = False
                continue
            elif line.startswith("Body:"):
                in_headers = False
                in_body = True
                continue
            if in_headers:
                if line.startswith("<") and line.endswith(">"):
                    # Truncated headers
                    continue
                elif line.startswith("{") and line.endswith("}"):
                    # Parse headers dict
                    try:
                        headers_str = line.replace("'", '"')
                        headers = json.loads(headers_str)
                        entry["headers"] = headers
                    except json.JSONDecodeError:
                        # Fallback: parse as key-value pairs
                        pass
                else:
                    # Parse as key: value format
                    if ":" in line:
                        key, value = line.split(":", 1)
                        entry["headers"][key.strip()] = value.strip()
            elif in_body:
                body_lines.append(line)
        if body_lines:
            entry["body"] = "\n".join(body_lines)
            entry["body_size"] = len(entry["body"])
        return entry
    except Exception as e:
        logger.error(f"Error parsing log block: {e}")
        return None


# --- Existing handlers ---
class ProxyHistoryHandler(APIRequestHandler):
    """Handler for proxy history."""

    def get(self):
        """Get proxy history entries."""
        try:
            entries = read_proxy_log()
            # Filter to only show requests (not responses)
            requests = [e for e in entries if e.get("direction") == "REQUEST"]
            self.write(requests)
        except Exception as e:
            logger.error(f"Error fetching proxy history: {e}")
            self.set_status(500)
            self.write({"error": f"Failed to fetch proxy history: {str(e)}"})


class ProxyHistoryDetailHandler(APIRequestHandler):
    """Handler for proxy history entry details."""

    def get(self, entry_id):
        """Get detailed information about a specific proxy entry."""
        try:
            # entry_id is actually the timestamp
            timestamp = entry_id
            logger.error(f"[ProxyHistoryDetailHandler.get] timestamp: {timestamp}")
            entries = read_proxy_log()
            print(f"[ProxyHistoryDetailHandler.get] entries: {entries}")
            logger.error(f"[ProxyHistoryDetailHandler.get] entries: {entries}")
            target_entry = None
            for entry in entries:
                if entry.get("timestamp") == timestamp:
                    target_entry = entry
                    break
            if not target_entry:
                print("[ProxyHistoryDetailHandler.get] Entry not found")
                logger.error("[ProxyHistoryDetailHandler.get] Entry not found")
                self.set_status(404)
                self.write({"error": "Entry not found"})
                return
            print(f"[ProxyHistoryDetailHandler.get] target_entry: {target_entry}")
            logger.error(
                f"[ProxyHistoryDetailHandler.get] target_entry: {target_entry}"
            )
            self.write(target_entry)
        except Exception as e:
            print(f"[ProxyHistoryDetailHandler.get] Exception: {e}")
            logger.error(f"[ProxyHistoryDetailHandler.get] Exception: {e}")
            self.set_status(500)
            self.write(
                {
                    "error": f"ProxyHistoryDetailHandler.get 500: Failed to fetch entry detail: {str(e)}"
                }
            )


class ProxyStatsHandler(APIRequestHandler):
    """Handler for proxy statistics."""

    def get(self):
        print("[ProxyStatsHandler.get] called")
        logger.error("[ProxyStatsHandler.get] called")
        try:
            entries = read_proxy_log()
            print(f"[ProxyStatsHandler.get] entries: {entries}")
            logger.error(f"[ProxyStatsHandler.get] entries: {entries}")
            stats = {
                "total_requests": len(
                    [e for e in entries if e.get("direction") == "REQUEST"]
                ),
                "total_responses": len(
                    [e for e in entries if e.get("direction") == "RESPONSE"]
                ),
                "http_requests": len(
                    [
                        e
                        for e in entries
                        if e.get("protocol") == "HTTP"
                        and e.get("direction") == "REQUEST"
                    ]
                ),
                "https_requests": len(
                    [
                        e
                        for e in entries
                        if e.get("protocol") == "HTTPS"
                        and e.get("direction") == "REQUEST"
                    ]
                ),
                "methods": {},
                "top_hosts": {},
                "status_codes": {},
            }
            for entry in entries:
                if entry.get("direction") == "REQUEST":
                    method = entry.get("method", "UNKNOWN")
                    stats["methods"][method] = stats["methods"].get(method, 0) + 1
                    url = entry.get("url", "")
                    if url:
                        try:
                            from urllib.parse import urlparse

                            host = urlparse(url).netloc
                            if host:
                                stats["top_hosts"][host] = stats["top_hosts"].get(
                                    host, 0
                                ) + 1
                        except:
                            pass
            for entry in entries:
                if entry.get("direction") == "RESPONSE":
                    status_code = entry.get("status_code", "UNKNOWN")
                    stats["status_codes"][status_code] = stats["status_codes"].get(
                        status_code, 0
                    ) + 1
            stats["top_hosts"] = dict(
                sorted(stats["top_hosts"].items(), key=lambda x: x[1], reverse=True)[
                    :10
                ]
            )
            print(f"[ProxyStatsHandler.get] stats: {stats}")
            logger.error(f"[ProxyStatsHandler.get] stats: {stats}")
            self.write(stats)
        except Exception as e:
            print(f"[ProxyStatsHandler.get] Exception: {e}")
            logger.error(f"[ProxyStatsHandler.get] Exception: {e}")
            self.set_status(500)
            self.write(
                {
                    "error": f"ProxyStatsHandler.get 500: Failed to fetch proxy statistics: {str(e)}"
                }
            )


class ProxyLogHandler(APIRequestHandler):
    """Handler for proxy log management."""

    def delete(self):
        print("[ProxyLogHandler.delete] called")
        logger.error("[ProxyLogHandler.delete] called")
        try:
            if os.path.exists(REQUEST_LOG_FILE):
                with open(REQUEST_LOG_FILE, "w") as f:
                    f.write("")
                print("[ProxyLogHandler.delete] Proxy log cleared successfully")
                logger.error("[ProxyLogHandler.delete] Proxy log cleared successfully")
                self.write({"message": "Proxy log cleared successfully"})
            else:
                print("[ProxyLogHandler.delete] No log file to clear")
                logger.error("[ProxyLogHandler.delete] No log file to clear")
                self.write({"message": "No log file to clear"})
        except Exception as e:
            print(f"[ProxyLogHandler.delete] Exception: {e}")
            logger.error(f"[ProxyLogHandler.delete] Exception: {e}")
            self.set_status(500)
            self.write(
                {
                    "error": f"ProxyLogHandler.delete 500: Failed to clear proxy log: {str(e)}"
                }
            )


# --- New Interceptor Management Handlers ---
class InterceptorManagementHandler(APIRequestHandler):
    """Handler for interceptor management."""

    def get(self):
        """Get all active interceptors."""
        try:
            # Get interceptor manager from the application
            if (
                hasattr(self.application, "interceptor_manager")
                and self.application.interceptor_manager
            ):
                interceptors = self.application.interceptor_manager.get_interceptors()
                self.write(json.dumps(interceptors))
            else:
                self.write(json.dumps([]))
        except Exception as e:
            logger.error(f"Error fetching interceptors: {e}")
            self.set_status(500)
            self.write({"error": f"Failed to fetch interceptors: {str(e)}"})

    def post(self):
        """Create new interceptor."""
        try:
            data = json.loads(self.request.body)
            interceptor_type = data.get("type")
            config = data.get("config", {})
            name = data.get("name", f"Custom {interceptor_type}")

            if (
                not hasattr(self.application, "interceptor_manager")
                or not self.application.interceptor_manager
            ):
                self.set_status(500)
                self.write({"error": "Interceptor manager not available"})
                return

            # Create interceptor based on type
            from owtf.proxy.interceptors import (
                HeaderModifier,
                BodyModifier,
                URLRewriter,
                DelayInjector,
            )

            interceptor_map = {
                "header": HeaderModifier,
                "body": BodyModifier,
                "url": URLRewriter,
                "delay": DelayInjector,
            }

            if interceptor_type not in interceptor_map:
                self.set_status(400)
                self.write({"error": f"Unknown interceptor type: {interceptor_type}"})
                return

            interceptor_class = interceptor_map[interceptor_type]
            interceptor = interceptor_class(**config)
            interceptor.name = name

            # Add to manager
            self.application.interceptor_manager.add_interceptor(interceptor)

            # Save configuration
            self.application.interceptor_manager.save_config()

            self.write({"status": "success", "id": interceptor.name})

        except Exception as e:
            logger.error(f"Error creating interceptor: {e}")
            self.set_status(500)
            self.write({"error": f"Failed to create interceptor: {str(e)}"})

    def delete(self, interceptor_id):
        """Remove interceptor."""
        try:
            if (
                not hasattr(self.application, "interceptor_manager")
                or not self.application.interceptor_manager
            ):
                self.set_status(500)
                self.write({"error": "Interceptor manager not available"})
                return

            self.application.interceptor_manager.remove_interceptor(interceptor_id)
            self.application.interceptor_manager.save_config()

            self.write({"status": "success"})

        except Exception as e:
            logger.error(f"Error removing interceptor: {e}")
            self.set_status(500)
            self.write({"error": f"Failed to remove interceptor: {str(e)}"})


class InterceptorConfigHandler(APIRequestHandler):
    """Handler for interceptor configuration."""

    def get(self, interceptor_id):
        """Get interceptor configuration."""
        try:
            if (
                not hasattr(self.application, "interceptor_manager")
                or not self.application.interceptor_manager
            ):
                self.set_status(500)
                self.write({"error": "Interceptor manager not available"})
                return

            interceptor = self.application.interceptor_manager.get_interceptor(
                interceptor_id
            )
            if not interceptor:
                self.set_status(404)
                self.write({"error": "Interceptor not found"})
                return

            config = {
                "id": interceptor.name,
                "name": interceptor.name,
                "enabled": interceptor.is_enabled(),
                "priority": interceptor.priority,
                "config": interceptor.get_config(),
            }

            self.write(config)

        except Exception as e:
            logger.error(f"Error fetching interceptor config: {e}")
            self.set_status(500)
            self.write({"error": f"Failed to fetch interceptor config: {str(e)}"})

    def put(self, interceptor_id):
        """Update interceptor configuration."""
        try:
            data = json.loads(self.request.body)

            if (
                not hasattr(self.application, "interceptor_manager")
                or not self.application.interceptor_manager
            ):
                self.set_status(500)
                self.write({"error": "Interceptor manager not available"})
                return

            interceptor = self.application.interceptor_manager.get_interceptor(
                interceptor_id
            )
            if not interceptor:
                self.set_status(404)
                self.write({"error": "Interceptor not found"})
                return

            # Update configuration
            if "config" in data:
                interceptor.set_config(data["config"])

            # Update enabled status
            if "enabled" in data:
                if data["enabled"]:
                    interceptor.enable()
                else:
                    interceptor.disable()

            # Update priority
            if "priority" in data:
                interceptor.priority = data["priority"]

            # Save configuration
            self.application.interceptor_manager.save_config()

            self.write({"status": "success"})

        except Exception as e:
            logger.error(f"Error updating interceptor config: {e}")
            self.set_status(500)
            self.write({"error": f"Failed to update interceptor config: {str(e)}"})


class InterceptorToggleHandler(APIRequestHandler):
    """Handler for toggling interceptor status."""

    def post(self, interceptor_id):
        """Toggle interceptor enabled/disabled status."""
        try:
            if (
                not hasattr(self.application, "interceptor_manager")
                or not self.application.interceptor_manager
            ):
                self.set_status(500)
                self.write({"error": "Interceptor manager not available"})
                return

            interceptor = self.application.interceptor_manager.get_interceptor(
                interceptor_id
            )
            if not interceptor:
                self.set_status(404)
                self.write({"error": "Interceptor not found"})
                return

            # Toggle status
            if interceptor.is_enabled():
                interceptor.disable()
                status = "disabled"
            else:
                interceptor.enable()
                status = "enabled"

            # Save configuration
            self.application.interceptor_manager.save_config()

            self.write({"status": "success", "interceptor_status": status})

        except Exception as e:
            logger.error(f"Error toggling interceptor: {e}")
            self.set_status(500)
            self.write({"error": f"Failed to toggle interceptor: {str(e)}"})


class InterceptorStatusHandler(APIRequestHandler):
    """Handler for interceptor system status."""

    def get(self):
        """Get overall interceptor system status."""
        try:
            if (
                not hasattr(self.application, "interceptor_manager")
                or not self.application.interceptor_manager
            ):
                self.write(
                    {
                        "status": "unavailable",
                        "message": "Interceptor manager not initialized",
                    }
                )
                return

            status = self.application.interceptor_manager.get_status()
            self.write(status)

        except Exception as e:
            logger.error(f"Error fetching interceptor status: {e}")
            self.set_status(500)
            self.write({"error": f"Failed to fetch interceptor status: {str(e)}"})


class InterceptionRulesHandler(APIRequestHandler):
    """Handler for interception rules."""

    def get(self):
        """Get all interception rules."""
        try:
            if (
                not hasattr(self.application, "interceptor_manager")
                or not self.application.interceptor_manager
            ):
                self.write(json.dumps([]))
                return

            rules = self.application.interceptor_manager.get_rules()
            self.write(json.dumps(rules))

        except Exception as e:
            logger.error(f"Error fetching interception rules: {e}")
            self.set_status(500)
            self.write({"error": f"Failed to fetch interception rules: {str(e)}"})

    def post(self):
        """Create new interception rule."""
        try:
            data = json.loads(self.request.body)

            if (
                not hasattr(self.application, "interceptor_manager")
                or not self.application.interceptor_manager
            ):
                self.set_status(500)
                self.write({"error": "Interceptor manager not available"})
                return

            # Generate unique ID for the rule
            import uuid

            rule_id = str(uuid.uuid4())
            data["id"] = rule_id

            self.application.interceptor_manager.add_rule(data)
            self.application.interceptor_manager.save_config()

            self.write({"status": "success", "id": rule_id})

        except Exception as e:
            logger.error(f"Error creating interception rule: {e}")
            self.set_status(500)
            self.write({"error": f"Failed to create interception rule: {str(e)}"})

    def delete(self, rule_id):
        """Delete interception rule."""
        try:
            if (
                not hasattr(self.application, "interceptor_manager")
                or not self.application.interceptor_manager
            ):
                self.set_status(500)
                self.write({"error": "Interceptor manager not available"})
                return

            self.application.interceptor_manager.remove_rule(rule_id)
            self.application.interceptor_manager.save_config()

            self.write({"status": "success"})

        except Exception as e:
            logger.error(f"Error deleting interception rule: {e}")
            self.set_status(500)
            self.write({"error": f"Failed to delete interception rule: {str(e)}"})


class RepeaterRequestHandler(APIRequestHandler):
    """Handler for sending HTTP requests from the Repeater tab"""

    async def post(self):
        """Send an HTTP request and return the response"""
        try:
            data = json.loads(self.request.body)

            # Extract request details
            method = data.get("method", "GET")
            url = data.get("url", "")
            headers = data.get("headers", {})
            body = data.get("body", "")

            if not url:
                self.set_status(400)
                self.write({"error": "URL is required"})
                return

            # Validate URL
            try:
                from urllib.parse import urlparse

                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise ValueError("Invalid URL")
            except Exception as e:
                self.set_status(400)
                self.write({"error": f"Invalid URL: {str(e)}"})
                return

            # Send request using aiohttp (async HTTP client)
            import aiohttp
            import asyncio
            import time

            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                # Prepare request kwargs
                request_kwargs = {
                    "headers": headers, "timeout": aiohttp.ClientTimeout(total=30)
                }  # 30 second timeout

                # Add body for methods that support it
                if method in ["POST", "PUT", "PATCH"] and body:
                    request_kwargs["data"] = body

                # Send request
                async with session.request(method, url, **request_kwargs) as response:
                    # Read response body
                    try:
                        response_body = await response.text()
                    except:
                        response_body = "[Unable to read response body]"

                    # Calculate response time
                    response_time = (
                        time.time() - start_time
                    ) * 1000  # Convert to milliseconds

                    # Convert response headers to dict
                    response_headers = dict(response.headers)

                    # Create response object
                    response_data = {
                        "status": response.status,
                        "statusText": response.reason,
                        "headers": response_headers,
                        "body": response_body,
                        "timestamp": datetime.now().isoformat(),
                        "responseTime": round(response_time, 2),
                    }

                    self.write(response_data)

        except json.JSONDecodeError:
            self.set_status(400)
            self.write({"error": "Invalid JSON"})
        except Exception as e:
            self.set_status(500)
            self.write({"error": f"Failed to send request: {str(e)}"})
