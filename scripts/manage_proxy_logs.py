#!/usr/bin/env python3
"""
Proxy Log Management Script

This script helps manage the OWTF proxy request logs to prevent disk space issues.
"""

import os
import sys
import argparse
import subprocess

LOG_FILE = "/tmp/owtf_requests.log"


def check_log_size():
    """Check the current size of the log file"""
    if os.path.exists(LOG_FILE):
        size = os.path.getsize(LOG_FILE)
        size_mb = size / (1024 * 1024)
        print(f"Log file size: {size_mb:.1f} MB")

        # Count lines
        try:
            result = subprocess.run(["wc", "-l", LOG_FILE], capture_output=True, text=True)
            lines = int(result.stdout.split()[0])
            print(f"Number of lines: {lines:,}")
        except:
            print("Could not count lines")
    else:
        print("Log file does not exist")


def clean_log():
    """Clean the log file"""
    try:
        with open(LOG_FILE, "w") as f:
            f.write(f"--- LOG FILE CLEANED ON {os.popen('date').read().strip()} ---\n")
        print("Log file cleaned")
    except Exception as e:
        print(f"Error cleaning log file: {e}")


def truncate_log(max_mb=10):
    """Truncate log file to specified size in MB"""
    if not os.path.exists(LOG_FILE):
        print("Log file does not exist")
        return

    current_size = os.path.getsize(LOG_FILE)
    max_size = max_mb * 1024 * 1024

    if current_size <= max_size:
        print(f"Log file is already smaller than {max_mb}MB")
        return

    try:
        with open(LOG_FILE, "r+b") as f:
            f.seek(-max_size, 2)  # Go to max_size bytes from end
            f.truncate()
            f.write(b"\n--- LOG FILE TRUNCATED ---\n")
        print(f"Log file truncated to {max_mb}MB")
    except Exception as e:
        print(f"Error truncating log file: {e}")


def show_log_stats():
    """Show statistics about the log file"""
    if not os.path.exists(LOG_FILE):
        print("Log file does not exist")
        return

    try:
        # Count HTTPS entries
        result = subprocess.run(["grep", "-c", "HTTPS", LOG_FILE], capture_output=True, text=True)
        https_count = int(result.stdout.strip())

        # Count HTTP entries
        result = subprocess.run(["grep", "-c", "HTTP REQUEST", LOG_FILE], capture_output=True, text=True)
        http_count = int(result.stdout.strip())

        # Count CONNECT entries
        result = subprocess.run(["grep", "-c", "CONNECT", LOG_FILE], capture_output=True, text=True)
        connect_count = int(result.stdout.strip())

        print(f"HTTPS entries: {https_count:,}")
        print(f"HTTP entries: {http_count:,}")
        print(f"CONNECT entries: {connect_count:,}")

    except Exception as e:
        print(f"Error getting log stats: {e}")


def main():
    parser = argparse.ArgumentParser(description="Manage OWTF proxy request logs")
    parser.add_argument("action", choices=["check", "clean", "truncate", "stats"], help="Action to perform")
    parser.add_argument("--max-mb", type=int, default=10, help="Maximum size in MB for truncate action (default: 10)")

    args = parser.parse_args()

    if args.action == "check":
        check_log_size()
    elif args.action == "clean":
        clean_log()
    elif args.action == "truncate":
        truncate_log(args.max_mb)
    elif args.action == "stats":
        show_log_stats()


if __name__ == "__main__":
    main()
