# OWTF Proxy Logging System

## Overview

This document describes the actual logging system implemented in the OWTF proxy. The logging system provides comprehensive request/response tracking, HTTPS interception logging, and performance monitoring for debugging and analysis purposes.

## What's Actually Implemented

### 1. Simple Text-Based Logging
- **Human-readable format** for easy debugging
- **Single log file** (`/tmp/owtf/request_response.log`)
- **Rate limiting** to prevent disk space issues
- **Automatic cleanup** when files get too large

### 2. Request/Response Tracking
- **HTTP requests**: Method, URL, headers, body preview
- **HTTP responses**: Status codes, headers, body preview
- **HTTPS interception**: CONNECT requests and SSL handshakes
- **WebSocket connections**: WebSocket upgrade requests

### 3. HTTPS Interception Logging
- **SSL handshake tracking** for client and upstream connections
- **Bidirectional forwarding** monitoring
- **Connection lifecycle** logging (connect, handshake, forward, close)
- **Error tracking** for SSL/TLS issues

### 4. Performance and Debugging
- **Rate limiting**: Configurable entries per minute
- **File rotation**: Automatic log file management
- **Error handling**: Graceful logging failure handling
- **Memory protection**: Prevents excessive disk usage

## Architecture

### Core Components

1. **`log_request()` function**: Main logging function for requests/responses
2. **`log_response()` function**: Wrapper for response logging
3. **Rate limiting system**: Prevents log flooding
4. **File rotation**: Manages log file sizes
5. **Error handling**: Graceful logging failure recovery

### Log File Structure

```
/tmp/owtf/
└── request_response.log    # Main log file (10MB max, 5 backups)
```

## Configuration

### Logging Settings

```python
# Located in owtf/proxy/proxy.py
REQUEST_LOG_FILE = "/tmp/owtf/request_response.log"
ENABLE_REQUEST_LOGGING = True  # Set to False to disable logging entirely
MAX_LOG_ENTRIES_PER_MINUTE = 100  # Limit logging rate
```

### File Management

- **Maximum file size**: 10MB per log file
- **Backup files**: 5 backup files (request_response.log.1, .2, etc.)
- **Automatic cleanup**: Truncates files larger than 50MB
- **Directory creation**: Automatically creates `/tmp/owtf/` if needed

## Usage

### Basic Logging

The logging functions are automatically called throughout the proxy:

```python
# Request logging (called automatically in get(), post(), etc.)
log_request(
    self.request,           # Request object
    method,                 # HTTP method (GET, POST, etc.)
    url,                    # Full URL
    headers,                # Request headers
    body,                   # Request body
    is_https,              # Boolean for HTTPS
)

# Response logging (called automatically after responses)
log_response(
    status_code,           # HTTP status code
    url,                   # Response URL
    headers,               # Response headers
    body,                  # Response body
    is_https,             # Boolean for HTTPS
)
```

### Manual Logging Control

```python
from owtf.proxy.proxy import (
    disable_request_logging,
    enable_request_logging,
    set_logging_rate_limit
)

# Disable logging entirely
disable_request_logging()

# Re-enable logging
enable_request_logging()

# Set custom rate limit
set_logging_rate_limit(200)  # 200 entries per minute
```

## Log Entry Examples

### HTTP Request
```
[2025-08-23 20:22:23] HTTP REQUEST GET https://www.google.com/async/hpba?yv=3&cs=1&ei=HiGqaJO-E6K4mtkP2KmxkQs&async=_basejs:/xjs/_/js/k%3Dxjs.hd.en.MGFpxmQcmbA.2018.O/am%3DAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAgACAAAAAEBAAAAAACCAPAAAAAAAAAAAAAAQQAAAMAAAAAAAAAAgAAIAAAAAIABAgACECIAAAwAAAAAAAAAAAAAgAEIAAAAEBgA_BkYAQAgIAEAAAAAAAAAAC4AAAkAABAAAAAAAAAAAAAAAIAAAAAAAAABAACAAAAACgAAAAAAAAAAAAAIAAAAAAAAACAAAAIgAAAAAAAAAAAAAAAgAAAAPQAAAAAAAAsAAAAAAAAAAAAOAEAIAAAA9igaAAAAAAAAAB0AAg8YUnMAAAAAAAAAAAAAAAAAAAABCoK5kEBAgAAAAAAAAAAAAAAAAAAAAAAAgFBNLCQ/dg%3D0/br%3D1/rs%3DACT90oHjZGQb4yXhNdNuZlFCO_lzrj5URQ,_basecss:/xjs/_/ss/k%3Dxjs.hd.ZPW53D7zfss.L.F4.O/am%3DAAKUCgQAAAAAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAQAAAAACAAAgIAABgAAR2CAAAAIADAPA0AAUAACAACAAAAIAAAMAAAAAAAAAEiGCAgABAAAKbBgACECIAAAgAAAAEAAgQIAAAEgEZAACQFBAFAAAAgEmgAQAICEAAAABAAyAAAAgAAAAAAAAAAAAAAAAAAAAAAIAAAAABBICLIASECoCkA4CCCAAAAABAAICAAAAAEAAQAAYEAIMAwhsAsAAAACAhAAAgPQCgAAACAAuBAAAAAAAAgABGAMAAACQA9igaAAAAAAAAABAAAAAAACMAAAAAAAAAAAAAAAAAAAABAAKIAEAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAIA/br%3D1/rs%3DACT90oGfwElwKesUERz6H4EZdQyESvw6ow
Headers: <8 headers, truncated>
--------------------------------------------------------------------------------
```

### HTTPS CONNECT Request
```
[2025-08-23 20:22:23] HTTPS REQUEST CONNECT www.google.com:443
Headers: {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0', 'Proxy-Connection': 'keep-alive', 'Connection': 'keep-alive', 'Host': 'www.google.com:443'}
--------------------------------------------------------------------------------
```

### HTTP Response
```
[2025-08-23 20:22:26] HTTPS RESPONSE HTTP/408 https://play.google.com
Headers: {'Content-Type': 'text/html; charset=UTF-8', 'Referrer-Policy': 'no-referrer', 'Content-Length': '1557', 'Date': 'Sat, 23 Aug 2025 20:22:26 GMT', 'Alt-Svc': 'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000', 'Connection': 'close'}
--------------------------------------------------------------------------------
```

## HTTPS Interception Logging

### SSL Handshake Tracking

The proxy logs detailed information about HTTPS interception:

```
[MITM] Received CONNECT for www.google.com:443
[MITM] Sent 200 Connection established to client for www.google.com:443
[MITM] SSL handshake with client successful for www.google.com:443
[MITM] SSL handshake with upstream www.google.com:443 successful
[MITM] Starting bidirectional forwarding for www.google.com:443
```

### Connection Lifecycle

```
[MITM] Connecting to upstream www.google.com:443
[MITM] Connected to upstream www.google.com:443, starting SSL handshake
[MITM] client->upstream forwarded 1024 bytes
[MITM] upstream->client forwarded 2048 bytes
[MITM] client connection closed gracefully
[MITM] upstream connection closed gracefully
```

## Performance Features

### Rate Limiting
- **Default limit**: 100 log entries per minute
- **Configurable**: Can be adjusted at runtime
- **Automatic reset**: Counter resets every minute
- **Graceful degradation**: Skips logging when limit exceeded

### File Management
- **Automatic rotation**: 10MB max file size
- **Backup retention**: 5 backup files
- **Emergency cleanup**: Truncates files larger than 50MB
- **Directory protection**: Creates log directory if missing

### Memory Protection
- **Header truncation**: Limits header logging to 2000 characters
- **Body preview**: Limits body logging to 500 bytes/characters
- **Error handling**: Graceful failure if logging fails
- **Resource cleanup**: Automatic file handle management

## Integration Points

### Automatic Logging

The logging is automatically integrated into:

1. **HTTP Methods**: `get()`, `post()`, `put()`, `delete()`, etc.
2. **HTTPS Interception**: `connect()` method for SSL tunneling
3. **WebSocket Support**: WebSocket upgrade requests
4. **Interceptor System**: Request/response modification tracking

### Manual Logging

Developers can manually log custom events:

```python
from owtf.proxy.proxy import log_request

# Log custom event
log_request(
    None,                    # No request object
    "CUSTOM_EVENT",         # Custom method
    "https://example.com",  # URL
    {"X-Custom": "value"},  # Headers
    "Custom data",          # Body
    True,                   # Is HTTPS
)
```

## Monitoring and Analysis

### Real-time Monitoring

```bash
# Watch live logs
tail -f /tmp/owtf/request_response.log

# Monitor specific patterns
tail -f /tmp/owtf/request_response.log | grep "HTTPS REQUEST"

# Check for errors
tail -f /tmp/owtf/request_response.log | grep "ERROR"
```

### Log Analysis

```bash
# Count requests by method
grep "HTTP REQUEST" /tmp/owtf/request_response.log | awk '{print $4}' | sort | uniq -c

# Find slow responses (HTTP 408 timeouts)
grep "HTTP/408" /tmp/owtf/request_response.log

# Analyze HTTPS traffic
grep "HTTPS" /tmp/owtf/request_response.log | wc -l
```

## Troubleshooting

### Common Issues

1. **Log file not created**
   - Check `/tmp/owtf/` directory permissions
   - Verify `ENABLE_REQUEST_LOGGING = True`

2. **High disk usage**
   - Check log file sizes: `ls -lh /tmp/owtf/`
   - Reduce rate limit: `set_logging_rate_limit(50)`
   - Disable logging: `disable_request_logging()`

3. **Performance impact**
   - Monitor logging overhead
   - Adjust rate limits as needed
   - Consider disabling for high-traffic scenarios

### Debug Mode

Enable debug logging for more detailed information:

```python
import logging
logger = logging.getLogger("owtf.proxy.proxy")
logger.setLevel(logging.DEBUG)
```

## Configuration Options

### Environment Variables

```bash
# Disable logging entirely
export OWTF_DISABLE_REQUEST_LOGGING=1

# Set custom log file location
export OWTF_REQUEST_LOG_FILE=/var/log/owtf/proxy.log

# Set custom rate limit
export OWTF_LOG_RATE_LIMIT=200
```

### Runtime Configuration

```python
from owtf.proxy.proxy import (
    ENABLE_REQUEST_LOGGING,
    MAX_LOG_ENTRIES_PER_MINUTE,
    REQUEST_LOG_FILE
)

# Check current settings
print(f"Logging enabled: {ENABLE_REQUEST_LOGGING}")
print(f"Rate limit: {MAX_LOG_ENTRIES_PER_MINUTE}")
print(f"Log file: {REQUEST_LOG_FILE}")
```

## Future Enhancements

### Planned Features
- **Structured logging**: JSON format for machine parsing
- **Log aggregation**: Centralized log collection
- **Performance metrics**: Response time tracking
- **Alerting**: Automated alerts for errors

### Extensibility
- **Custom loggers**: Add new log types
- **Plugin system**: Extend logging capabilities
- **API endpoints**: REST API for log access
- **Export formats**: Support for additional formats

## Conclusion

The OWTF proxy logging system provides comprehensive visibility into proxy operations with a focus on simplicity and reliability. The text-based format makes debugging straightforward, while the rate limiting and file management ensure the system remains stable under high load.

For questions or issues, refer to the logging functions in `owtf/proxy/proxy.py` and the test scripts provided in the proxy module.

