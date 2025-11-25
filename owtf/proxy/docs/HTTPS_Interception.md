# OWTF Proxy HTTPS Interception

## Overview

The OWTF proxy provides comprehensive HTTPS interception capabilities, allowing security testers to inspect and modify encrypted HTTPS traffic in real-time. This document explains how the HTTPS interception system works, how to configure it, and how to troubleshoot common issues.

## How HTTPS Interception Works

### Man-in-the-Middle (MITM) Architecture

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│   Browser   │    │   OWTF Proxy    │    │ Target     │
│             │    │                 │    │ Server     │
│ HTTPS      │◄──►│ SSL Client      │◄──►│ HTTPS      │
│ (Port 443) │    │ SSL Server      │    │ (Port 443) │
└─────────────┘    └─────────────────┘    └─────────────┘
```

### SSL Handshake Flow

1. **Browser CONNECT Request**: Browser sends `CONNECT example.com:443 HTTP/1.1`
2. **Proxy Response**: Proxy responds with `HTTP/1.1 200 Connection established`
3. **Client SSL Handshake**: Proxy establishes SSL connection with browser using generated certificate
4. **Upstream SSL Handshake**: Proxy establishes SSL connection with target server
5. **Bidirectional Relay**: Proxy forwards encrypted data between browser and server

## Certificate Management

### Certificate Authority (CA)

**Purpose**: Root certificate that signs all generated domain certificates

**Location**: `/home/owtf/.owtf/proxy/certs/ca.crt`
**Private Key**: `/home/owtf/.owtf/proxy/certs/ca.key`
**Password**: `owtf123`

**Generation**: Automatically created on first proxy startup

### Domain Certificates

**Purpose**: Individual certificates for each intercepted domain

**Location**: `/home/owtf/.owtf/proxy/certs/`
**Naming Convention**: `domain_com.crt` and `domain_com.key`
**Validity**: 1 year from generation
**Auto-generation**: Created on-demand when domains are accessed

### Certificate Features

**Subject Alternative Names (SANs)**:
- Main domain (e.g., `example.com`)
- WWW subdomain (e.g., `www.example.com`)
- Wildcard subdomains (e.g., `*.example.com`)
- Localhost variations (`localhost`, `127.0.0.1`, `0.0.0.0`)

**Certificate Details**:
- **Country**: US
- **State**: Pwnland
- **Organization**: OWTF
- **Organizational Unit**: Inbound-Proxy
- **Common Name**: Domain being intercepted

## Configuration

### Basic Setup

**1. Install CA Certificate**:
```bash
# Download CA certificate
curl -o ca.crt http://localhost:8009/api/v1/proxy/ca-cert/

# Install in browser/system
# For Firefox: Settings → Privacy & Security → View Certificates → Authorities → Import
# For Chrome: Settings → Privacy and security → Security → Manage certificates → Authorities → Import
```

**2. Configure Browser Proxy**:
- **HTTP Proxy**: `localhost:8008`
- **HTTPS Proxy**: `localhost:8008`
- **SOCKS Proxy**: Not supported

**3. Trust CA Certificate**:
- Mark the downloaded CA certificate as trusted
- Accept security warnings for intercepted sites

### Advanced Configuration

**Custom Certificate Paths**:
```python
# In owtf/proxy/main.py
CA_CERT_PATH = "/custom/path/ca.crt"
CA_KEY_PATH = "/custom/path/ca.key"
CERT_FOLDER = "/custom/path/certs/"
```

**Certificate Generation Options**:
```python
# In owtf/proxy/gen_cert.py
CERT_VALIDITY_DAYS = 365
KEY_SIZE = 2048
SIGNATURE_ALGORITHM = "sha256"
```

## Implementation Details

### Core Components

#### 1. HTTPS Interceptor (`https_interceptor.py`)

**Main Class**: `HTTPSInterceptor`

**Key Methods**:
- `intercept_https_connection()`: Main interception logic
- `create_ssl_context()`: SSL context creation
- `handle_ssl_handshake()`: SSL handshake management
- `bidirectional_relay()`: Data forwarding between client and server

#### 2. Socket Wrapper (`socket_wrapper.py`)

**Main Function**: `starttls()`

**Purpose**: Handles SSL/TLS handshakes with non-blocking support

**Features**:
- Async SSL handshake support
- Error handling and recovery
- Callback-based success/failure handling

#### 3. Certificate Generator (`gen_cert.py`)

**Main Function**: `generate_certificate()`

**Purpose**: Generates SSL certificates for intercepted domains

**Features**:
- Automatic SAN generation
- Proper date handling
- Key size and algorithm configuration

### SSL Context Configuration

**Client Context (Browser → Proxy)**:
```python
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(cert_file, key_file)
ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')
```

**Server Context (Proxy → Target)**:
```python
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
```

## Usage Examples

### Basic HTTPS Interception

**1. Start the Proxy**:
```bash
# Start OWTF proxy
docker exec -it owtf-backend python -c "from owtf.proxy.main import start_proxy; start_proxy()"
```

**2. Configure Browser**:
- Set proxy to `localhost:8008`
- Install CA certificate
- Trust the CA certificate

**3. Browse HTTPS Sites**:
- Navigate to any HTTPS site
- Accept security warnings
- Traffic is now intercepted and logged

### Testing HTTPS Interception

**Using curl**:
```bash
# Test HTTPS interception
curl -x http://localhost:8008 -k https://httpbin.org/get

# Test with custom headers
curl -x http://localhost:8008 -k https://httpbin.org/headers \
  -H "X-Test-Header: test-value"

# Test POST requests
curl -x http://localhost:8008 -k https://httpbin.org/post \
  -d '{"test": "data"}' \
  -H "Content-Type: application/json"
```

**Using Python**:
```python
import requests

proxies = {
    'http': 'http://localhost:8008',
    'https': 'http://localhost:8008'
}

# Test HTTPS request
response = requests.get('https://httpbin.org/get', 
                       proxies=proxies, 
                       verify=False)
print(response.status_code)
print(response.text)
```

## Monitoring and Logging

### Log Files

**Main Log**: `/tmp/owtf/request_response.log`

**HTTPS Interception Logs**:
```
[2025-08-23 20:22:23] HTTPS REQUEST CONNECT www.google.com:443
Headers: {'User-Agent': 'Mozilla/5.0...', 'Host': 'www.google.com:443'}
--------------------------------------------------------------------------------
```

**SSL Handshake Logs**:
```
[MITM] Received CONNECT for www.google.com:443
[MITM] SSL handshake with client successful for www.google.com:443
[MITM] SSL handshake with upstream www.google.com:443 successful
[MITM] Starting bidirectional forwarding for www.google.com:443
```

### Real-time Monitoring

**Watch Live Logs**:
```bash
# Monitor all HTTPS traffic
tail -f /tmp/owtf/request_response.log | grep "HTTPS"

# Monitor SSL handshakes
tail -f /tmp/owtf/request_response.log | grep "MITM"

# Monitor specific domain
tail -f /tmp/owtf/request_response.log | grep "google.com"
```

**Performance Metrics**:
```bash
# Count HTTPS requests
grep "HTTPS REQUEST" /tmp/owtf/request_response.log | wc -l

# Count SSL handshakes
grep "MITM.*successful" /tmp/owtf/request_response.log | wc -l

# Find failed connections
grep "MITM.*failed" /tmp/owtf/request_response.log
```

## Troubleshooting

### Common Issues

#### 1. Certificate Errors

**Problem**: Browser shows "Certificate is not trusted" or "Domain mismatch"

**Solutions**:
```bash
# Regenerate CA certificate
docker exec -it owtf-backend python /home/owtf/fix_certificates.py

# Regenerate domain certificates
docker exec -it owtf-backend python /home/owtf/regenerate_certificates.py

# Restart OWTF completely
docker restart owtf-backend
```

**Verification**:
```bash
# Check CA certificate
openssl x509 -in /home/owtf/.owtf/proxy/certs/ca.crt -text -noout

# Check domain certificate
openssl x509 -in /home/owtf/.owtf/proxy/certs/example_com.crt -text -noout
```

#### 2. SSL Handshake Failures

**Problem**: `SSL routines::wrong version number` errors

**Solutions**:
```bash
# Check proxy is running
netstat -tlnp | grep 8008

# Restart proxy completely
docker restart owtf-backend

# Check proxy logs
tail -f /tmp/owtf/request_response.log
```

#### 3. Connection Timeouts

**Problem**: HTTP 408 Request Timeout errors

**Solutions**:
```bash
# Check proxy performance
tail -f /tmp/owtf/request_response.log | grep "HTTP/408"

# Reduce logging rate
docker exec -it owtf-backend python -c "
from owtf.proxy.proxy import set_logging_rate_limit
set_logging_rate_limit(50)
"

# Check system resources
docker exec -it owtf-backend top
```

#### 4. HSTS Issues

**Problem**: Sites with HSTS policy fail to load

**Solutions**:
```bash
# Verify certificates have proper dates
openssl x509 -in /home/owtf/.owtf/proxy/certs/ca.crt -noout -dates

# Check for future dates and regenerate if needed
docker exec -it owtf-backend python /home/owtf/fix_certificates.py
```

### Debug Mode

**Enable Debug Logging**:
```python
import logging

# Enable debug for HTTPS interceptor
logger = logging.getLogger("owtf.proxy.https_interceptor")
logger.setLevel(logging.DEBUG)

# Enable debug for socket wrapper
logger = logging.getLogger("owtf.proxy.socket_wrapper")
logger.setLevel(logging.DEBUG)
```

**Verbose SSL Output**:
```bash
# Test with verbose SSL output
curl -x http://localhost:8008 -k -v https://httpbin.org/get

# Check SSL handshake details
openssl s_client -connect localhost:8008 -proxy localhost:8008
```

### Performance Issues

**Connection Limits**:
```python
# In proxy configuration
MAX_CONCURRENT_CONNECTIONS = 100
CONNECTION_TIMEOUT = 30
SSL_HANDSHAKE_TIMEOUT = 10
```

**Buffer Management**:
```python
# Buffer sizes for data forwarding
CLIENT_BUFFER_SIZE = 4096
SERVER_BUFFER_SIZE = 4096
MAX_BUFFER_SIZE = 1024 * 1024  # 1MB
```

## Security Considerations

### Certificate Security

**CA Private Key Protection**:
- Store CA private key securely
- Use strong password protection
- Limit access to key files
- Regular key rotation

**Domain Certificate Management**:
- Automatic cleanup of expired certificates
- Secure storage of private keys
- Certificate validation before use

### Traffic Security

**Data Protection**:
- All intercepted data is logged
- Secure log file access
- Log rotation and cleanup
- Access control for log files

**Privacy Considerations**:
- Inform users about interception
- Secure storage of sensitive data
- Compliance with privacy regulations
- Audit logging of all activities

## Advanced Features

### Custom Certificate Authorities

**Using External CA**:
```python
# Configure external CA
EXTERNAL_CA_CERT = "/path/to/external/ca.crt"
EXTERNAL_CA_KEY = "/path/to/external/ca.key"
EXTERNAL_CA_PASSWORD = "password"
```

**Certificate Chain Management**:
```python
# Load intermediate certificates
ssl_context.load_verify_locations(cafile="/path/to/ca-bundle.crt")
```

### Protocol Support

**TLS Versions**:
- TLS 1.0 (deprecated but supported)
- TLS 1.1 (deprecated but supported)
- TLS 1.2 (recommended)
- TLS 1.3 (latest, supported)

**Cipher Suites**:
- Modern cipher suites by default
- Configurable cipher preferences
- Fallback to compatible ciphers

### Performance Optimization

**Connection Pooling**:
- Reuse upstream connections
- Keep-alive support
- Connection multiplexing
- Resource cleanup

**Async Processing**:
- Non-blocking SSL operations
- Event-driven I/O
- Efficient buffer management
- Minimal memory overhead

## Testing and Validation

### Automated Testing

**Test Scripts**:
```bash
# Run comprehensive HTTPS tests
python owtf/proxy/test_https_interception.py

# Or if running from the proxy directory
cd owtf/proxy
python test_https_interception.py

# Test specific components
python -m pytest tests/test_https_interception.py
```

**Test Coverage**:
- Basic HTTPS interception
- Custom headers and body
- POST requests with JSON
- Large response handling
- Error condition testing

### Manual Testing

**Browser Testing**:
- Test with different browsers
- Verify certificate installation
- Check HSTS compatibility
- Test various HTTPS sites

**Tool Testing**:
- Test with curl, wget, Python requests
- Verify proxy authentication
- Check error handling
- Test performance under load

