# OWTF Proxy Interceptor System

## Overview

The OWTF proxy interceptor system provides a flexible framework for modifying HTTP requests and responses in real-time. Interceptors can be used for security testing, debugging, traffic analysis, and automated request manipulation.

## Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   HTTP Request  │───►│  Interceptor     │───►│ Modified Request│
│                 │    │   Manager        │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Interceptors   │
                       │   (Priority      │
                       │    Based)        │
                       └──────────────────┘
```

### Interceptor Types

1. **Request Interceptors**: Modify outgoing requests
2. **Response Interceptors**: Modify incoming responses
3. **Static Interceptors**: Pre-configured rules
4. **Live Interceptors**: Real-time, interactive modification

## Static Interceptors

### 1. Header Modifier (`header_modifier.py`)

**Purpose**: Add, remove, or modify HTTP headers

**Configuration**:
```json
{
  "name": "Add Security Headers",
  "type": "header_modifier",
  "priority": 100,
  "rules": [
    {
      "action": "add",
      "header": "X-Forwarded-For",
      "value": "192.168.1.100"
    },
    {
      "action": "remove",
      "header": "User-Agent"
    },
    {
      "action": "modify",
      "header": "Accept",
      "value": "text/html,application/xhtml+xml"
    }
  ]
}
```

**Actions**:
- `add`: Add new header
- `remove`: Remove existing header
- `modify`: Change header value

**Use Cases**:
- Add authentication headers
- Remove identifying headers
- Modify content negotiation
- Add security headers

### 2. Body Modifier (`body_modifier.py`)

**Purpose**: Transform request/response body content

**Configuration**:
```json
{
  "name": "JSON Body Modifier",
  "type": "body_modifier",
  "priority": 200,
  "rules": [
    {
      "action": "replace",
      "pattern": "password123",
      "replacement": "newpassword456"
    },
    {
      "action": "append",
      "content": "&debug=true"
    }
  ]
}
```

**Actions**:
- `replace`: Replace text patterns
- `append`: Add content to end
- `prepend`: Add content to beginning
- `remove`: Remove content matching pattern

**Use Cases**:
- Password replacement
- Debug parameter injection
- Content sanitization
- Payload modification

### 3. URL Rewriter (`url_rewriter.py`)

**Purpose**: Modify request URLs and paths

**Configuration**:
```json
{
  "name": "API Version Rewriter",
  "type": "url_rewriter",
  "priority": 150,
  "rules": [
    {
      "action": "rewrite",
      "pattern": "/api/v1/",
      "replacement": "/api/v2/"
    },
    {
      "action": "redirect",
      "pattern": "/old/",
      "replacement": "/new/"
    }
  ]
}
```

**Actions**:
- `rewrite`: Change URL path
- `redirect`: Send redirect response
- `add_param`: Add query parameters
- `remove_param`: Remove query parameters

**Use Cases**:
- API version switching
- Path rewriting
- Query parameter manipulation
- A/B testing

### 4. Delay Injector (`delay_injector.py`)

**Purpose**: Add artificial delays to requests/responses

**Configuration**:
```json
{
  "name": "Slow Response Simulator",
  "type": "delay_injector",
  "priority": 300,
  "rules": [
    {
      "action": "delay",
      "pattern": "/api/slow/",
      "delay_ms": 5000
    },
    {
      "action": "random_delay",
      "pattern": "/api/random/",
      "min_delay_ms": 1000,
      "max_delay_ms": 10000
    }
  ]
}
```

**Actions**:
- `delay`: Fixed delay in milliseconds
- `random_delay`: Random delay within range
- `conditional_delay`: Delay based on conditions

**Use Cases**:
- Performance testing
- Race condition testing
- Load testing
- User experience simulation

## Live Interceptor

### Overview

The live interceptor provides real-time, interactive request interception that allows users to manually inspect and modify requests before they are forwarded.

### Features

- **Pattern Matching**: URL and method-based filtering
- **Real-time Modification**: Live header and body editing
- **Decision Management**: Forward, modify, or drop requests
- **Timeout Handling**: Automatic forwarding on timeout
- **Request Queuing**: Handle multiple pending requests

### Configuration

```python
from owtf.proxy.live_interceptor import LiveInterceptor

# Create live interceptor
li = LiveInterceptor()

# Enable for specific pattern
li.enable_interception(
    url_pattern="https://example.com/api/*",
    methods=["GET", "POST"],
    timeout=30
)

# Disable interception
li.disable_interception()
```

### API Usage

**Enable Interception**:
```bash
curl -X POST http://localhost:8009/api/v1/proxy/live-interceptor/enable \
  -H "Content-Type: application/json" \
  -d '{
    "url_pattern": "https://example.com/*",
    "methods": ["GET", "POST"],
    "timeout": 30
  }'
```

**Get Pending Requests**:
```bash
curl http://localhost:8009/api/v1/proxy/live-interceptor/pending
```

**Make Decision**:
```bash
curl -X POST http://localhost:8009/api/v1/proxy/live-interceptor/decision \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "uuid-here",
    "decision": "forward",
    "modified_headers": {},
    "modified_body": ""
  }'
```

## Interceptor Manager

### Overview

The interceptor manager coordinates the execution of all interceptors, handling registration, priority management, and configuration persistence.

### Key Functions

```python
from owtf.proxy.interceptor_manager import InterceptorManager

# Create manager
im = InterceptorManager()

# Add interceptor
im.add_interceptor(interceptor)

# Remove interceptor
im.remove_interceptor(interceptor_id)

# Enable/disable interceptor
im.enable_interceptor(interceptor_id)
im.disable_interceptor(interceptor_id)

# Get all interceptors
interceptors = im.get_interceptors()

# Apply interceptors to request
modified_request = im.intercept_request(request)
```

### Priority System

Interceptors are executed in priority order:

1. **Priority 1000+**: System interceptors (logging, security)
2. **Priority 500-999**: High-priority custom interceptors
3. **Priority 100-499**: Standard interceptors
4. **Priority 1-99**: Low-priority interceptors

### Configuration Persistence

**Configuration File**: `/home/owtf/.owtf/proxy/interceptor_config.json`

**Auto-save**: Configuration is automatically saved when modified
**Backup**: Previous configuration is backed up before changes
**Validation**: Configuration is validated before loading

## Creating Custom Interceptors

### Base Interceptor Class

```python
from owtf.proxy.interceptors.base import BaseInterceptor

class CustomInterceptor(BaseInterceptor):
    def __init__(self, name, priority=100):
        super().__init__(name, priority)
        self.type = "custom"
    
    def intercept_request(self, request):
        # Modify request here
        return request
    
    def intercept_response(self, response):
        # Modify response here
        return response
    
    def get_config(self):
        return {
            "name": self.name,
            "type": self.type,
            "priority": self.priority
        }
```

### Required Methods

- `intercept_request(request)`: Modify outgoing request
- `intercept_response(response)`: Modify incoming response
- `get_config()`: Return configuration dictionary
- `validate_config(config)`: Validate configuration (optional)

### Example Custom Interceptor

```python
class SecurityHeadersInterceptor(BaseInterceptor):
    def __init__(self):
        super().__init__("Security Headers", priority=1000)
        self.type = "security_headers"
    
    def intercept_request(self, request):
        # Add security headers
        request.headers["X-Content-Type-Options"] = "nosniff"
        request.headers["X-Frame-Options"] = "DENY"
        request.headers["X-XSS-Protection"] = "1; mode=block"
        return request
    
    def intercept_response(self, response):
        # Add security headers to response
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
```

## Configuration Examples

### Complete Interceptor Configuration

```json
{
  "interceptors": [
    {
      "id": "security_headers",
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
    },
    {
      "id": "debug_injector",
      "name": "Debug Parameter Injector",
      "type": "url_rewriter",
      "priority": 500,
      "enabled": true,
      "rules": [
        {
          "action": "add_param",
          "param": "debug",
          "value": "true"
        }
      ]
    }
  ],
  "live_interceptor": {
    "enabled": false,
    "url_pattern": "",
    "methods": [],
    "timeout": 30
  }
}
```

### Environment-Specific Configurations

**Development**:
```json
{
  "interceptors": [
    {
      "name": "Development Headers",
      "type": "header_modifier",
      "priority": 100,
      "rules": [
        {
          "action": "add",
          "header": "X-Environment",
          "value": "development"
        }
      ]
    }
  ]
}
```

**Testing**:
```json
{
  "interceptors": [
    {
      "name": "Test Data Injector",
      "type": "body_modifier",
      "priority": 200,
      "rules": [
        {
          "action": "replace",
          "pattern": "{{TEST_USER}}",
          "replacement": "testuser123"
        }
      ]
    }
  ]
}
```

## Best Practices

### Performance Considerations

1. **Priority Ordering**: Place high-priority interceptors first
2. **Efficient Patterns**: Use efficient regex patterns
3. **Conditional Execution**: Only run interceptors when needed
4. **Resource Cleanup**: Clean up resources after use

### Security Considerations

1. **Input Validation**: Validate all configuration inputs
2. **Access Control**: Restrict interceptor modification access
3. **Logging**: Log all interceptor actions for audit
4. **Error Handling**: Gracefully handle interceptor failures

### Maintenance

1. **Regular Review**: Review interceptor configurations regularly
2. **Testing**: Test interceptors in staging environment
3. **Documentation**: Document custom interceptor behavior
4. **Backup**: Keep backup of working configurations

## Troubleshooting

### Common Issues

1. **Interceptor Not Working**
   - Check if interceptor is enabled
   - Verify priority ordering
   - Check pattern matching
   - Review configuration syntax

2. **Performance Issues**
   - Reduce interceptor complexity
   - Optimize pattern matching
   - Check resource usage
   - Review priority ordering

3. **Configuration Errors**
   - Validate JSON syntax
   - Check required fields
   - Verify file permissions
   - Review error logs

### Debug Mode

Enable debug logging for interceptors:

```python
import logging
logger = logging.getLogger("owtf.proxy.interceptor_manager")
logger.setLevel(logging.DEBUG)
```

### Testing Interceptors

Use the test scripts to verify interceptor functionality:

```bash
# Test specific interceptor
python -m pytest tests/test_interceptors.py::test_header_modifier

# Test all interceptors
python -m pytest tests/test_interceptors.py
```