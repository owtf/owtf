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
                        entry["headers"] = json.loads(headers_str)
                    except:
                        pass
            elif in_body:
                if line.startswith("<") and line.endswith(">"):
                    # Truncated body
                    size_match = re.search(r"<(\d+) bytes", line)
                    if size_match:
                        entry["body_size"] = int(size_match.group(1))
                    entry["body"] = line
                    break
                else:
                    body_lines.append(line)
                    entry["body"] = "\n".join(body_lines)
                    entry["body_size"] = len(entry["body"])
        # Add status code for responses
        if direction == "RESPONSE" and method.startswith("HTTP/"):
            try:
                status_code = method.split("/")[1]
                entry["status_code"] = status_code
            except:
                pass
        return entry
    except Exception as e:
        logger.error(f"Error parsing log block: {e}")
        return None


class ProxyHistoryHandler(APIRequestHandler):
    """Handler for proxy request/response history."""

    def get(self):
        print("[ProxyHistoryHandler.get] called")
        logger.error("[ProxyHistoryHandler.get] called")
        try:
            # Get query parameters
            limit = int(self.get_argument("limit", default="100"))
            offset = int(self.get_argument("offset", default="0"))
            method_filter = self.get_argument("method", default=None)
            url_filter = self.get_argument("url", default=None)
            protocol_filter = self.get_argument("protocol", default=None)
            # Read and parse the log file
            print(f"[ProxyHistoryHandler.get] reading proxy log from {REQUEST_LOG_FILE}")
            logger.error(f"[ProxyHistoryHandler.get] reading proxy log from {REQUEST_LOG_FILE}")
            entries = read_proxy_log()
            print(f"[ProxyHistoryHandler.get] entries: {entries}")
            logger.error(f"[ProxyHistoryHandler.get] entries: {entries}")
            # Apply filters
            if method_filter:
                entries = [entry for entry in entries if method_filter.upper() in entry.get("method", "")]
            if url_filter:
                entries = [entry for entry in entries if url_filter.lower() in entry.get("url", "").lower()]
            if protocol_filter:
                entries = [entry for entry in entries if protocol_filter.upper() in entry.get("protocol", "")]
            # Apply pagination
            total_count = len(entries)
            entries = entries[offset : offset + limit]
            # Prepare response
            response = {
                "entries": entries,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count,
            }
            print(f"[ProxyHistoryHandler.get] response: {response}")
            logger.error(f"[ProxyHistoryHandler.get] response: {response}")
            self.write(response)
        except Exception as e:
            print(f"[ProxyHistoryHandler.get] Exception: {e}")
            logger.error(f"[ProxyHistoryHandler.get] Exception: {e}")
            self.set_status(500)
            self.write({"error": f"ProxyHistoryHandler.get 500: Failed to fetch proxy history: {str(e)}"})


class ProxyHistoryDetailHandler(APIRequestHandler):
    """Handler for detailed proxy entry information."""

    def get(self, entry_id):
        print("[ProxyHistoryDetailHandler.get] called")
        logger.error("[ProxyHistoryDetailHandler.get] called")
        try:
            timestamp = entry_id
            print(f"[ProxyHistoryDetailHandler.get] timestamp: {timestamp}")
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
            logger.error(f"[ProxyHistoryDetailHandler.get] target_entry: {target_entry}")
            self.write(target_entry)
        except Exception as e:
            print(f"[ProxyHistoryDetailHandler.get] Exception: {e}")
            logger.error(f"[ProxyHistoryDetailHandler.get] Exception: {e}")
            self.set_status(500)
            self.write({"error": f"ProxyHistoryDetailHandler.get 500: Failed to fetch entry detail: {str(e)}"})


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
                "total_requests": len([e for e in entries if e.get("direction") == "REQUEST"]),
                "total_responses": len([e for e in entries if e.get("direction") == "RESPONSE"]),
                "http_requests": len(
                    [e for e in entries if e.get("protocol") == "HTTP" and e.get("direction") == "REQUEST"]
                ),
                "https_requests": len(
                    [e for e in entries if e.get("protocol") == "HTTPS" and e.get("direction") == "REQUEST"]
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
                                stats["top_hosts"][host] = stats["top_hosts"].get(host, 0) + 1
                        except:
                            pass
            for entry in entries:
                if entry.get("direction") == "RESPONSE":
                    status_code = entry.get("status_code", "UNKNOWN")
                    stats["status_codes"][status_code] = stats["status_codes"].get(status_code, 0) + 1
            stats["top_hosts"] = dict(sorted(stats["top_hosts"].items(), key=lambda x: x[1], reverse=True)[:10])
            print(f"[ProxyStatsHandler.get] stats: {stats}")
            logger.error(f"[ProxyStatsHandler.get] stats: {stats}")
            self.write(stats)
        except Exception as e:
            print(f"[ProxyStatsHandler.get] Exception: {e}")
            logger.error(f"[ProxyStatsHandler.get] Exception: {e}")
            self.set_status(500)
            self.write({"error": f"ProxyStatsHandler.get 500: Failed to fetch proxy statistics: {str(e)}"})


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
            self.write({"error": f"ProxyLogHandler.delete 500: Failed to clear proxy log: {str(e)}"})
