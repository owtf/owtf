#!/usr/bin/env python3
"""
Generate test proxy data for OWTF UI testing
"""

import datetime
import json
import os
import random
import time

# Sample data for testing
SAMPLE_REQUESTS = [
    {
        "method": "GET",
        "url": "https://example.com/",
        "protocol": "HTTPS",
        "direction": "REQUEST",
        "headers": {"User-Agent": "Mozilla/5.0", "Accept": "text/html"},
        "body": "",
        "body_size": 0,
    },
    {
        "method": "POST",
        "url": "https://api.example.com/login",
        "protocol": "HTTPS",
        "direction": "REQUEST",
        "headers": {"Content-Type": "application/json"},
        "body": '{"username": "test", "password": "test123"}',
        "body_size": 45,
    },
    {
        "method": "GET",
        "url": "http://test.local/css/style.css",
        "protocol": "HTTP",
        "direction": "REQUEST",
        "headers": {"Accept": "text/css"},
        "body": "",
        "body_size": 0,
    },
    {
        "method": "GET",
        "url": "https://cdn.example.com/js/app.js",
        "protocol": "HTTPS",
        "direction": "REQUEST",
        "headers": {"Accept": "application/javascript"},
        "body": "",
        "body_size": 0,
    },
]

SAMPLE_RESPONSES = [
    {
        "method": "GET",
        "url": "https://example.com/",
        "protocol": "HTTPS",
        "direction": "RESPONSE",
        "status_code": "200",
        "headers": {"Content-Type": "text/html", "Server": "nginx"},
        "body": "<html><body>Hello World</body></html>",
        "body_size": 35,
    },
    {
        "method": "POST",
        "url": "https://api.example.com/login",
        "protocol": "HTTPS",
        "direction": "RESPONSE",
        "status_code": "401",
        "headers": {"Content-Type": "application/json"},
        "body": '{"error": "Invalid credentials"}',
        "body_size": 28,
    },
    {
        "method": "GET",
        "url": "http://test.local/css/style.css",
        "protocol": "HTTP",
        "direction": "RESPONSE",
        "status_code": "200",
        "headers": {"Content-Type": "text/css"},
        "body": "body { color: red; }",
        "body_size": 20,
    },
    {
        "method": "GET",
        "url": "https://cdn.example.com/js/app.js",
        "protocol": "HTTPS",
        "direction": "RESPONSE",
        "status_code": "404",
        "headers": {"Content-Type": "text/plain"},
        "body": "File not found",
        "body_size": 13,
    },
]


def generate_log_entry(entry_data):
    """Generate a log entry with timestamp"""
    timestamp = datetime.datetime.now() - datetime.timedelta(
        seconds=random.randint(0, 3600)  # Random time within last hour
    )

    entry = entry_data.copy()
    entry["timestamp"] = timestamp.isoformat()

    # Format the log entry
    log_lines = [
        f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {entry['protocol']} {entry['direction']} {entry['method']} {entry['url']}",
        f"Headers: {entry['headers']}",
        f"Body: {entry['body']}",
        "-" * 80,
    ]

    return "\n".join(log_lines)


def create_test_log_file():
    """Create a test proxy log file with sample data"""
    log_file = "/tmp/owtf/request_response.log"

    # Ensure directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Generate log entries
    all_entries = []

    # Add some requests
    for request in SAMPLE_REQUESTS:
        all_entries.append(generate_log_entry(request))

    # Add some responses
    for response in SAMPLE_RESPONSES:
        all_entries.append(generate_log_entry(response))

    # Shuffle entries to make them more realistic
    random.shuffle(all_entries)

    # Write to file
    with open(log_file, "w") as f:
        f.write("\n".join(all_entries))

    print(f"Generated test proxy log with {len(all_entries)} entries")
    print(f"Log file: {log_file}")
    print("\nSample data includes:")
    print("   • 4 HTTP/HTTPS requests")
    print("   • 4 HTTP/HTTPS responses")
    print("   • Various status codes (200, 401, 404)")
    print("   • Different HTTP methods (GET, POST)")
    print("   • Sample headers and bodies")
    print("\nRefresh the OWTF proxy page to see the data!")


if __name__ == "__main__":
    print("Generating test proxy data for OWTF UI...")
    create_test_log_file()
