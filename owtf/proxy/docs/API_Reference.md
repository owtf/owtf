# OWTF Proxy API Reference

## Overview

The OWTF proxy provides a comprehensive REST API for managing proxy operations, interceptors, and monitoring. This document describes all available API endpoints, their parameters, and usage examples.

## Base URL

**Development**: `http://localhost:8009/api/v1/proxy/`
**Production**: `https://your-domain.com/api/v1/proxy/`

## Authentication

Currently, the API does not require authentication. However, it's recommended to implement authentication for production deployments.

## Common Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Response data here
  },
  "timestamp": "2025-08-23T20:30:00Z"
}
```

**Error Response Format**:
```json
{
  "success": false,
  "error": "Error description",
  "message": "Detailed error message",
  "timestamp": "2025-08-23T20:30:00Z"
}
```

## API Endpoints

### 1. Proxy History

#### Get Proxy History

**Endpoint**: `GET /history`

**Description**: Retrieves the proxy request/response history

**Query Parameters**:
- `limit` (optional): Number of entries to return (default: 100)
- `offset` (optional): Number of entries to skip (default: 0)
- `method` (optional): Filter by HTTP method
- `url` (optional): Filter by URL pattern
- `status_code` (optional): Filter by response status code
- `is_https` (optional): Filter by protocol (true/false)

**Example Request**:
```bash
curl "http://localhost:8009/api/v1/proxy/history?limit=50&method=POST"
```

**Example Response**:
```json
{
  "success": true,
  "message": "History retrieved successfully",
  "data": {
    "entries": [
      {
        "timestamp": "2025-08-23 20:22:23",
        "protocol": "HTTPS",
        "direction": "REQUEST",
        "method": "POST",
        "url": "https://httpbin.org/post",
        "headers": {
          "User-Agent": "curl/7.81.0",
          "Content-Type": "application/json"
        },
        "body_size": 25,
        "body_preview": "{\"test\": \"data\"}"
      }
    ],
    "total": 150,
    "limit": 50,
    "offset": 0
  }
}
```

#### Clear Proxy History

**Endpoint**: `DELETE /history`

**Description**: Clears all proxy history entries

**Example Request**:
```bash
curl -X DELETE "http://localhost:8009/api/v1/proxy/history"
```

**Example Response**:
```json
{
  "success": true,
  "message": "History cleared successfully",
  "data": {
    "cleared_entries": 150
  }
}
```

### 2. Proxy Statistics

#### Get Proxy Statistics

**Endpoint**: `GET /stats`

**Description**: Retrieves comprehensive proxy statistics

**Example Request**:
```bash
curl "http://localhost:8009/api/v1/proxy/stats"
```

**Example Response**:
```json
{
  "success": true,
  "message": "Statistics retrieved successfully",
  "data": {
    "total_requests": 1250,
    "total_responses": 1248,
    "http_requests": 800,
    "https_requests": 450,
    "successful_responses": 1200,
    "error_responses": 48,
    "methods": {
      "GET": 600,
      "POST": 400,
      "PUT": 150,
      "DELETE": 100
    },
    "status_codes": {
      "200": 1000,
      "404": 100,
      "500": 50,
      "408": 48
    },
    "top_domains": [
      "google.com",
      "httpbin.org",
      "example.com"
    ],
    "average_response_time_ms": 245.67,
    "requests_per_minute": 12.5
  }
}
```

### 3. CA Certificate Management

#### Download CA Certificate

**Endpoint**: `GET /ca-cert/`

**Description**: Downloads the Certificate Authority certificate for HTTPS interception

**Example Request**:
```bash
curl -o ca.crt "http://localhost:8009/api/v1/proxy/ca-cert/"
```

**Response**: Raw certificate file (PEM format)

**Example Certificate Content**:
```
-----BEGIN CERTIFICATE-----
MIIFhTCCA22gAwIBAgIUF1IOCHOMF1p7zkd+gouQNkaM0jgwDQYJKoZIhvcNAQEL
BQAwUjELMAkGA1UEBhMCVVMxEDAOBgNVBAgMB1B3bmxhbmQxDjAMBgNVBAcMBU9X
QVNQMQ0wCwYDVQQKDARPV1RGMRIwEAYDVQQDDAlNaVRNUHJveHkwHhcNMjUwODIz
MTk0MjQ4WhcNMzUwODIxMTk0MjQ4WjBSMQswCQYDVQQGEwJVUzEQMA4GA1UECAwH
...
-----END CERTIFICATE-----
```

### 4. Repeater

#### Send Request

**Endpoint**: `POST /repeater/`

**Description**: Sends a custom HTTP request through the proxy

**Request Body**:
```json
{
  "method": "POST",
  "url": "https://httpbin.org/post",
  "headers": {
    "User-Agent": "OWTF-Repeater/1.0",
    "Content-Type": "application/json"
  },
  "body": "{\"test\": \"data\"}",
  "follow_redirects": true,
  "timeout": 30
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:8009/api/v1/proxy/repeater/" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "POST",
    "url": "https://httpbin.org/post",
    "headers": {"User-Agent": "OWTF-Repeater/1.0"},
    "body": "{\"test\": \"data\"}"
  }'
```

**Example Response**:
```json
{
  "success": true,
  "message": "Request sent successfully",
  "data": {
    "request": {
      "method": "POST",
      "url": "https://httpbin.org/post",
      "headers": {
        "User-Agent": "OWTF-Repeater/1.0",
        "Content-Type": "application/json"
      },
      "body": "{\"test\": \"data\"}"
    },
    "response": {
      "status_code": 200,
      "headers": {
        "Content-Type": "application/json",
        "Server": "gunicorn/19.9.0"
      },
      "body": "{\"args\":{},\"data\":\"{\\\"test\\\": \\\"data\\\"}\",\"files\":{},\"form\":{},\"headers\":{\"Accept\":\"*/*\",\"Content-Type\":\"application/json\",\"Host\":\"httpbin.org\",\"User-Agent\":\"OWTF-Repeater/1.0\"},\"json\":{\"test\":\"data\"},\"origin\":\"99.100.157.119\",\"url\":\"https://httpbin.org/post\"}",
      "response_time_ms": 245.67
    }
  }
}
```

#### Get Repeater History

**Endpoint**: `GET /repeater/history`

**Description**: Retrieves the history of repeater requests

**Query Parameters**:
- `limit` (optional): Number of entries to return (default: 50)
- `offset` (optional): Number of entries to skip (default: 0)

**Example Request**:
```bash
curl "http://localhost:8009/api/v1/proxy/repeater/history?limit=10"
```

**Example Response**:
```json
{
  "success": true,
  "message": "Repeater history retrieved successfully",
  "data": {
    "entries": [
      {
        "id": "req_12345",
        "timestamp": "2025-08-23 20:30:00",
        "method": "POST",
        "url": "https://httpbin.org/post",
        "status_code": 200,
        "response_time_ms": 245.67
      }
    ],
    "total": 25,
    "limit": 10,
    "offset": 0
  }
}
```

### 5. Live Interceptor

#### Enable Interception

**Endpoint**: `POST /live-interceptor/enable`

**Description**: Enables live interception for specific URL patterns

**Request Body**:
```json
{
  "url_pattern": "https://example.com/api/*",
  "methods": ["GET", "POST", "PUT"],
  "timeout": 30
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:8009/api/v1/proxy/live-interceptor/enable" \
  -H "Content-Type: application/json" \
  -d '{
    "url_pattern": "https://example.com/api/*",
    "methods": ["GET", "POST"],
    "timeout": 30
  }'
```

**Example Response**:
```json
{
  "success": true,
  "message": "Live interception enabled successfully",
  "data": {
    "url_pattern": "https://example.com/api/*",
    "methods": ["GET", "POST"],
    "timeout": 30,
    "enabled": true
  }
}
```

#### Disable Interception

**Endpoint**: `POST /live-interceptor/disable`

**Description**: Disables live interception

**Example Request**:
```bash
curl -X POST "http://localhost:8009/api/v1/proxy/live-interceptor/disable"
```

**Example Response**:
```json
{
  "success": true,
  "message": "Live interception disabled successfully",
  "data": {
    "enabled": false
  }
}
```

#### Get Pending Requests

**Endpoint**: `GET /live-interceptor/pending`

**Description**: Retrieves pending intercepted requests

**Example Request**:
```bash
curl "http://localhost:8009/api/v1/proxy/live-interceptor/pending"
```

**Example Response**:
```json
{
  "success": true,
  "message": "Pending requests retrieved successfully",
  "data": {
    "requests": [
      {
        "id": "req_67890",
        "timestamp": "2025-08-23 20:35:00",
        "method": "POST",
        "url": "https://example.com/api/users",
        "headers": {
          "User-Agent": "Mozilla/5.0...",
          "Content-Type": "application/json"
        },
        "body": "{\"username\": \"testuser\"}",
        "timeout_at": "2025-08-23 20:35:30"
      }
    ],
    "total": 1
  }
}
```

#### Make Decision

**Endpoint**: `POST /live-interceptor/decision`

**Description**: Makes a decision for an intercepted request

**Request Body**:
```json
{
  "request_id": "req_67890",
  "decision": "forward",
  "modified_headers": {
    "X-Modified": "true"
  },
  "modified_body": "{\"username\": \"modified_user\"}"
}
```

**Decision Options**:
- `forward`: Forward the request as-is
- `modify`: Forward with modifications
- `drop`: Drop the request

**Example Request**:
```bash
curl -X POST "http://localhost:8009/api/v1/proxy/live-interceptor/decision" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_67890",
    "decision": "modify",
    "modified_headers": {"X-Modified": "true"},
    "modified_body": "{\"username\": \"modified_user\"}"
  }'
```

**Example Response**:
```json
{
  "success": true,
  "message": "Decision applied successfully",
  "data": {
    "request_id": "req_67890",
    "decision": "modify",
    "status": "processed"
  }
}
```

#### Get Interceptor Status

**Endpoint**: `GET /live-interceptor/status`

**Description**: Gets the current status of the live interceptor

**Example Request**:
```bash
curl "http://localhost:8009/api/v1/proxy/live-interceptor/status"
```

**Example Response**:
```json
{
  "success": true,
  "message": "Status retrieved successfully",
  "data": {
    "enabled": true,
    "url_pattern": "https://example.com/api/*",
    "methods": ["GET", "POST"],
    "timeout": 30,
    "pending_requests": 1,
    "total_intercepted": 15
  }
}
```

### 6. Interceptor Management

#### Get All Interceptors

**Endpoint**: `GET /interceptors/`

**Description**: Retrieves all configured interceptors

**Example Request**:
```bash
curl "http://localhost:8009/api/v1/proxy/interceptors/"
```

**Example Response**:
```json
{
  "success": true,
  "message": "Interceptors retrieved successfully",
  "data": {
    "interceptors": [
      {
        "id": "header_mod_1",
        "name": "Security Headers",
        "type": "header_modifier",
        "priority": 1000,
        "enabled": true,
        "rules": [
          {
            "action": "add",
            "header": "X-Content-Type-Options",
            "value": "nosniff"
          }
        ]
      }
    ],
    "total": 1
  }
}
```

#### Add Interceptor

**Endpoint**: `POST /interceptors/`

**Description**: Adds a new interceptor

**Request Body**:
```json
{
  "name": "Custom Header Modifier",
  "type": "header_modifier",
  "priority": 500,
  "enabled": true,
  "rules": [
    {
      "action": "add",
      "header": "X-Custom",
      "value": "custom-value"
    }
  ]
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:8009/api/v1/proxy/interceptors/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Custom Header Modifier",
    "type": "header_modifier",
    "priority": 500,
    "enabled": true,
    "rules": [{"action": "add", "header": "X-Custom", "value": "custom-value"}]
  }'
```

**Example Response**:
```json
{
  "success": true,
  "message": "Interceptor added successfully",
  "data": {
    "id": "interceptor_12345",
    "name": "Custom Header Modifier",
    "type": "header_modifier",
    "priority": 500,
    "enabled": true
  }
}
```

#### Update Interceptor

**Endpoint**: `PUT /interceptors/{id}`

**Description**: Updates an existing interceptor

**Example Request**:
```bash
curl -X PUT "http://localhost:8009/api/v1/proxy/interceptors/interceptor_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false
  }'
```

#### Delete Interceptor

**Endpoint**: `DELETE /interceptors/{id}`

**Description**: Deletes an interceptor

**Example Request**:
```bash
curl -X DELETE "http://localhost:8009/api/v1/proxy/interceptors/interceptor_12345"
```

### 7. System Information

#### Get System Status

**Endpoint**: `GET /status`

**Description**: Gets the overall system status

**Example Request**:
```bash
curl "http://localhost:8009/api/v1/proxy/status"
```

**Example Response**:
```json
{
  "success": true,
  "message": "Status retrieved successfully",
  "data": {
    "proxy_running": true,
    "proxy_port": 8008,
    "uptime_seconds": 3600,
    "total_requests": 1250,
    "active_connections": 5,
    "memory_usage_mb": 128.5,
    "disk_usage_mb": 45.2,
    "certificates": {
      "ca_valid": true,
      "ca_expires": "2026-08-23T19:42:48Z",
      "domain_certificates": 15
    },
    "interceptors": {
      "total": 5,
      "enabled": 3,
      "disabled": 2
    },
    "live_interceptor": {
      "enabled": true,
      "pending_requests": 1
    }
  }
}
```

## Error Codes

### HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Endpoint not found
- **500 Internal Server Error**: Server error

### Error Types

- **VALIDATION_ERROR**: Invalid input parameters
- **NOT_FOUND**: Resource not found
- **INTERNAL_ERROR**: Server internal error
- **TIMEOUT_ERROR**: Request timeout
- **CERTIFICATE_ERROR**: Certificate-related error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default Limit**: 100 requests per minute per IP
- **Burst Limit**: 10 requests per second
- **Headers**: Rate limit information included in response headers

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS):

- **Allowed Origins**: Configurable in settings
- **Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Allowed Headers**: Content-Type, Authorization
- **Credentials**: Supported

## WebSocket Support

Some endpoints support WebSocket connections for real-time updates:

- **Live Interceptor Events**: Real-time request interception notifications
- **Statistics Updates**: Live statistics updates
- **Log Streaming**: Real-time log streaming

## SDK Examples

### Python SDK

```python
import requests

class OWTFProxyAPI:
    def __init__(self, base_url="http://localhost:8009/api/v1/proxy"):
        self.base_url = base_url
    
    def get_history(self, limit=100, offset=0):
        params = {"limit": limit, "offset": offset}
        response = requests.get(f"{self.base_url}/history", params=params)
        return response.json()
    
    def send_repeater_request(self, method, url, headers=None, body=None):
        data = {
            "method": method,
            "url": url,
            "headers": headers or {},
            "body": body or ""
        }
        response = requests.post(f"{self.base_url}/repeater/", json=data)
        return response.json()
    
    def enable_live_interception(self, url_pattern, methods=None, timeout=30):
        data = {
            "url_pattern": url_pattern,
            "methods": methods or ["GET", "POST"],
            "timeout": timeout
        }
        response = requests.post(f"{self.base_url}/live-interceptor/enable", json=data)
        return response.json()

# Usage
api = OWTFProxyAPI()
history = api.get_history(limit=50)
print(f"Retrieved {len(history['data']['entries'])} history entries")
```

### JavaScript SDK

```javascript
class OWTFProxyAPI {
    constructor(baseUrl = 'http://localhost:8009/api/v1/proxy') {
        this.baseUrl = baseUrl;
    }
    
    async getHistory(limit = 100, offset = 0) {
        const params = new URLSearchParams({ limit, offset });
        const response = await fetch(`${this.baseUrl}/history?${params}`);
        return await response.json();
    }
    
    async sendRepeaterRequest(method, url, headers = {}, body = '') {
        const response = await fetch(`${this.baseUrl}/repeater/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ method, url, headers, body })
        });
        return await response.json();
    }
    
    async enableLiveInterception(urlPattern, methods = ['GET', 'POST'], timeout = 30) {
        const response = await fetch(`${this.baseUrl}/live-interceptor/enable`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url_pattern: urlPattern, methods, timeout })
        });
        return await response.json();
    }
}

// Usage
const api = new OWTFProxyAPI();
api.getHistory(50).then(history => {
    console.log(`Retrieved ${history.data.entries.length} history entries`);
});
```