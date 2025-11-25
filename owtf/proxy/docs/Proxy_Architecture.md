# OWTF Proxy Architecture

## Overview

The OWTF proxy is a comprehensive web application security testing proxy that provides HTTP/HTTPS interception, request/response modification, and real-time traffic analysis. This document describes the high-level architecture and how the various components interact.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   OWTF Proxy     │    │  Target Server  │
│                 │◄──►│                  │◄──►│                 │
│  (Client)      │    │  (Interceptor)   │    │  (Upstream)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Core Components

### 1. Main Entry Point (`main.py`)

**Purpose**: Initializes and starts the proxy server

**Key Functions**:
- `start_proxy()`: Main entry point for starting the proxy
- `create_application()`: Creates the Tornado web application
- `setup_certificates()`: Initializes SSL certificates for HTTPS interception

**Configuration**:
- Proxy port: 8008 (configurable)
- SSL certificate paths
- Interceptor manager initialization

### 2. Proxy Handler (`proxy.py`)

**Purpose**: Core request processing and routing logic

**Key Classes**:
- `ProxyHandler`: Main request handler for all HTTP methods
- `WebSocketHandler`: Handles WebSocket connections

**HTTP Methods Supported**:
- GET, POST, PUT, DELETE, HEAD, OPTIONS, TRACE, CONNECT

**Key Features**:
- Automatic request/response logging
- Interceptor integration
- Live interception support
- HTTPS tunneling and interception

### 3. HTTPS Interceptor (`https_interceptor.py`)

**Purpose**: Manages HTTPS traffic interception and SSL handshakes

**Key Functions**:
- `intercept_https_connection()`: Main HTTPS interception logic
- SSL context creation and management
- Bidirectional data forwarding
- Connection lifecycle management

**SSL Features**:
- Client certificate generation
- Upstream SSL connection handling
- Bidirectional data relay
- Error handling and recovery

### 4. Live Interceptor (`live_interceptor.py`)

**Purpose**: Provides real-time, interactive request interception

**Key Features**:
- Pattern-based request matching
- Real-time request modification
- User decision handling (forward/modify/drop)
- Timeout management
- Request queuing

**API Endpoints**:
- `/api/v1/proxy/live-interceptor/`: Main live interceptor API
- Request interception and modification
- Decision management

### 5. Interceptor Manager (`interceptor_manager.py`)

**Purpose**: Manages the lifecycle of static interceptors

**Key Features**:
- Interceptor registration and management
- Priority-based execution
- Configuration persistence
- Rule-based interception

**Supported Interceptors**:
- Header modifiers
- Body modifiers
- URL rewriters
- Delay injectors

### 6. Socket Wrapper (`socket_wrapper.py`)

**Purpose**: Handles SSL/TLS handshakes and socket operations

**Key Functions**:
- `starttls()`: Initiates SSL handshake
- SSL context creation
- Non-blocking handshake support
- Error handling and recovery

## Data Flow

### HTTP Request Flow

```
1. Browser → Proxy (HTTP Request)
2. Proxy → Interceptor Manager (Apply interceptors)
3. Proxy → Live Interceptor (Check for live interception)
4. Proxy → Target Server (Forward modified request)
5. Target Server → Proxy (Response)
6. Proxy → Interceptor Manager (Apply response interceptors)
7. Proxy → Browser (Modified response)
```

### HTTPS Request Flow

```
1. Browser → Proxy (CONNECT request)
2. Proxy → Browser (200 Connection established)
3. Browser → Proxy (SSL handshake)
4. Proxy → Target Server (SSL handshake)
5. Proxy ↔ Target Server (Bidirectional SSL relay)
6. Proxy ↔ Browser (Bidirectional SSL relay)
```

### Interceptor Flow

```
1. Request received
2. Check interceptor rules
3. Apply matching interceptors (priority order)
4. Forward modified request
5. Receive response
6. Apply response interceptors
7. Return modified response
```

## Configuration Management

### Certificate Management

**CA Certificate**:
- Location: `/home/owtf/.owtf/proxy/certs/ca.crt`
- Private key: `/home/owtf/.owtf/proxy/certs/ca.key`
- Password: `owtf123`

**Domain Certificates**:
- Auto-generated per domain
- Include Subject Alternative Names (SANs)
- Valid for 1 year
- Stored in `/home/owtf/.owtf/proxy/certs/`

### Logging Configuration

**Log File**: `/tmp/owtf/request_response.log`
**Rate Limiting**: 100 entries per minute
**File Rotation**: 10MB max, 5 backup files
**Emergency Cleanup**: Truncates files >50MB

### Interceptor Configuration

**Configuration File**: `/home/owtf/.owtf/proxy/interceptor_config.json`
**Default Interceptors**: Header, Body, URL, Delay modifiers
**Priority System**: Higher numbers = higher priority

## Security Features

### HTTPS Interception

- **Man-in-the-Middle (MITM)**: Full SSL/TLS interception
- **Certificate Generation**: Dynamic per-domain certificates
- **SAN Support**: Comprehensive domain name coverage
- **HSTS Compatibility**: Works with strict security policies

### Request Filtering

- **Pattern Matching**: URL and method-based filtering
- **Header Modification**: Add/remove/modify headers
- **Body Modification**: Content transformation
- **Rate Limiting**: Prevent abuse and DoS

### Access Control

- **CORS Support**: Cross-origin request handling
- **Authentication**: Optional authentication for live interceptor
- **IP Filtering**: Configurable client IP restrictions

## Performance Considerations

### Connection Management

- **Connection Pooling**: Reuse upstream connections
- **Keep-Alive**: Maintain persistent connections
- **Timeout Handling**: Configurable connection timeouts
- **Resource Cleanup**: Automatic connection cleanup

### Memory Management

- **Buffer Limits**: Configurable buffer sizes
- **Log Rotation**: Prevent disk space issues
- **Rate Limiting**: Control memory usage
- **Garbage Collection**: Automatic cleanup

### Scalability

- **Async I/O**: Non-blocking request handling
- **Thread Safety**: Safe concurrent access
- **Load Balancing**: Support for multiple upstream servers
- **Horizontal Scaling**: Multiple proxy instances

## Error Handling

### SSL/TLS Errors

- **Handshake Failures**: Graceful fallback to HTTP
- **Certificate Errors**: Automatic certificate regeneration
- **Connection Errors**: Retry logic and error reporting
- **Timeout Handling**: Configurable timeouts

### Network Errors

- **Connection Refused**: Upstream server unavailable
- **DNS Resolution**: Domain name resolution failures
- **Network Timeouts**: Connection timeout handling
- **Proxy Errors**: Internal proxy error handling

### Application Errors

- **Interceptor Failures**: Graceful degradation
- **Configuration Errors**: Default fallback values
- **Resource Exhaustion**: Automatic cleanup and recovery
- **Logging Failures**: Non-blocking error handling

## Monitoring and Debugging

### Log Analysis

- **Request Patterns**: Analyze traffic patterns
- **Error Tracking**: Monitor error rates and types
- **Performance Metrics**: Response time analysis
- **Security Events**: Track suspicious activities

### Health Checks

- **Certificate Validity**: Monitor certificate expiration
- **Connection Status**: Check upstream connectivity
- **Resource Usage**: Monitor memory and disk usage
- **Error Rates**: Track error frequency

### Debug Tools

- **Live Interceptor**: Real-time request inspection
- **Log Monitoring**: Tail log files for debugging
- **Certificate Inspection**: View and validate certificates
- **Network Testing**: Test connectivity and SSL

## Deployment Considerations

### System Requirements

- **Python**: 3.8+ recommended
- **Memory**: Minimum 512MB, 1GB+ recommended
- **Disk Space**: 100MB+ for certificates and logs
- **Network**: Stable internet connection for upstream

### Security Considerations

- **Firewall Rules**: Restrict access to proxy port
- **Certificate Security**: Secure CA private key storage
- **Access Control**: Limit proxy access to authorized users
- **Log Security**: Secure log file access and rotation

### Performance Tuning

- **Buffer Sizes**: Optimize for expected traffic patterns
- **Timeout Values**: Balance responsiveness and stability
- **Rate Limits**: Adjust based on system capacity
- **Log Levels**: Optimize logging for production use

## Future Enhancements

### Planned Features

- **Response Interception**: Modify response content
- **Advanced Filtering**: Content-based request filtering
- **Performance Metrics**: Detailed performance monitoring
- **API Enhancements**: RESTful API for configuration

### Extensibility

- **Plugin System**: Custom interceptor development
- **Custom Protocols**: Support for additional protocols
- **Integration APIs**: Third-party tool integration
- **Cloud Deployment**: Container and cloud support

