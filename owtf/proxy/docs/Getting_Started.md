# OWTF Proxy - Getting Started Guide

## Overview

The OWTF proxy is a powerful web application security testing proxy that provides HTTP/HTTPS interception, request/response modification, and real-time traffic analysis. This guide will help you get started with the proxy quickly and efficiently.

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows (WSL2 recommended for Windows)
- **Python**: 3.8 or higher
- **Memory**: Minimum 512MB RAM, 1GB+ recommended
- **Disk Space**: 100MB+ for certificates and logs
- **Network**: Stable internet connection

### Required Software

- **Docker**: For containerized deployment
- **Git**: For source code management
- **Web Browser**: Chrome, Firefox, or Edge for testing

## Installation

### Option 1: Docker Deployment (Recommended)

**1. Clone the Repository**:
```bash
git clone https://github.com/owtf/owtf.git
cd owtf
```

**2. Build and Start the Container**:
```bash
# Build the OWTF container
docker build -t owtf-backend .

# Start the container
docker run -d --name owtf-backend \
  -p 8008:8008 \
  -p 8009:8009 \
  -v $(pwd)/.owtf:/home/owtf/.owtf \
  owtf-backend
```

**3. Verify Installation**:
```bash
# Check if container is running
docker ps | grep owtf-backend

# Check proxy port
docker exec -it owtf-backend netstat -tlnp | grep 8008
```

### Option 2: Local Development Setup

**1. Clone and Setup**:
```bash
git clone https://github.com/owtf/owtf.git
cd owtf

# Create virtual environment
python -m venv owtf-venv
source owtf-venv/bin/activate  # On Windows: owtf-venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**2. Start the Proxy**:
```bash
# Start the proxy
python -m owtf.proxy.main
```

## Basic Configuration

### 1. Browser Proxy Configuration

**Firefox**:
1. Go to `Settings` → `General` → `Network Settings`
2. Click `Settings...`
3. Select `Manual proxy configuration`
4. Set HTTP Proxy: `localhost`, Port: `8008`
5. Set HTTPS Proxy: `localhost`, Port: `8008`
6. Check `Use this proxy server for all protocols`
7. Click `OK`

**Chrome**:
1. Go to `Settings` → `Advanced` → `System`
2. Click `Open your computer's proxy settings`
3. Set HTTP Proxy: `localhost:8008`
4. Set HTTPS Proxy: `localhost:8008`
5. Click `Save`

### 2. Install CA Certificate

**Download Certificate**:
```bash
# Download the CA certificate
curl -o ca.crt http://localhost:8009/api/v1/proxy/ca-cert/
```

**Install in Browser**:

**Firefox**:
1. Go to `Settings` → `Privacy & Security`
2. Scroll down to `Certificates`
3. Click `View Certificates...`
4. Go to `Authorities` tab
5. Click `Import...`
6. Select the downloaded `ca.crt` file
7. Check `Trust this CA to identify websites`
8. Click `OK`

**Chrome**:
1. Go to `Settings` → `Privacy and security` → `Security`
2. Click `Manage certificates`
3. Go to `Authorities` tab
4. Click `Import...`
5. Select the downloaded `ca.crt` file
6. Check `Trust this certificate authority for identifying websites`
7. Click `OK`

### 3. Verify Configuration

**Test HTTP Proxy**:
```bash
# Test HTTP proxy
curl -x http://localhost:8008 http://httpbin.org/get
```

**Test HTTPS Proxy**:
```bash
# Test HTTPS proxy (should work after CA installation)
curl -x http://localhost:8008 https://httpbin.org/get
```

## First Use

### 1. Basic HTTP Interception

**1. Start Browsing**:
- Open your configured browser
- Navigate to any HTTP site (e.g., `http://httpbin.org`)
- The proxy will automatically intercept and log the traffic

**2. Check Logs**:
```bash
# View proxy logs
docker exec -it owtf-backend tail -f /tmp/owtf/request_response.log

# Or if running locally
tail -f /tmp/owtf/request_response.log
```

**3. View History**:
- Open `http://localhost:8009` in your browser
- Navigate to the Proxy tab
- View intercepted requests in the History tab

### 2. HTTPS Interception

**1. Test HTTPS Site**:
- Navigate to an HTTPS site (e.g., `https://httpbin.org`)
- Accept any security warnings (this is normal for intercepted traffic)
- The proxy will now intercept encrypted HTTPS traffic

**2. Verify Interception**:
```bash
# Check for HTTPS logs
docker exec -it owtf-backend tail -f /tmp/owtf/request_response.log | grep "HTTPS"
```

### 3. Using the Repeater

**1. Access Repeater**:
- Go to `http://localhost:8009`
- Navigate to the Proxy tab → Repeater tab

**2. Send a Test Request**:
- Set Method: `GET`
- Set URL: `https://httpbin.org/get`
- Click `Send Request`
- View the response in the Response section

**3. Modify and Resend**:
- Change the URL to `https://httpbin.org/headers`
- Add a custom header: `X-Test: test-value`
- Click `Send Request` again

## Common Tasks

### 1. View Proxy Statistics

**Via Web Interface**:
- Go to `http://localhost:8009` → Proxy tab
- View statistics in the Statistics section

**Via API**:
```bash
curl http://localhost:8009/api/v1/proxy/stats
```

### 2. Clear Proxy History

**Via Web Interface**:
- Go to Proxy tab → History tab
- Click `Clear History` button

**Via API**:
```bash
curl -X DELETE http://localhost:8009/api/v1/proxy/history
```

### 3. Configure Interceptors

**1. Access Interceptor Management**:
- Go to Proxy tab → Interceptors tab
- View existing interceptors

**2. Add Header Modifier**:
- Click `Add Interceptor`
- Set Type: `Header Modifier`
- Set Name: `Security Headers`
- Add Rule: Action `add`, Header `X-Content-Type-Options`, Value `nosniff`
- Click `Save`

**3. Test Interceptor**:
- Send a request through the proxy
- Check that the security header was added

### 4. Use Live Interceptor

**1. Enable Live Interception**:
- Go to Proxy tab → Interceptors tab
- In the Live Interceptor section, set:
  - URL Pattern: `https://example.com/*`
  - Methods: `GET, POST`
  - Timeout: `30`
- Click `Enable`

**2. Intercept Requests**:
- Navigate to a matching URL
- The request will be intercepted
- View pending requests in the Live Interceptor section

**3. Make Decisions**:
- For each intercepted request, choose:
  - `Forward`: Send as-is
  - `Modify`: Edit headers/body before sending
  - `Drop`: Block the request

## Troubleshooting

### Common Issues

#### 1. Proxy Not Starting

**Problem**: Container fails to start or proxy port not listening

**Solutions**:
```bash
# Check container logs
docker logs owtf-backend

# Check if port is in use
netstat -tlnp | grep 8008

# Restart container
docker restart owtf-backend
```

#### 2. Certificate Errors

**Problem**: Browser shows "Certificate is not trusted"

**Solutions**:
```bash
# Regenerate certificates
docker exec -it owtf-backend python /home/owtf/fix_certificates.py

# Restart OWTF
docker restart owtf-backend

# Reinstall CA certificate in browser
```

#### 3. HTTPS Not Working

**Problem**: HTTPS sites fail to load

**Solutions**:
```bash
# Check proxy logs
docker exec -it owtf-backend tail -f /tmp/owtf/request_response.log

# Verify CA certificate installation
# Check browser proxy settings
# Ensure CA certificate is trusted
```

#### 4. Performance Issues

**Problem**: Slow response times or timeouts

**Solutions**:
```bash
# Check system resources
docker exec -it owtf-backend top

# Reduce logging rate
docker exec -it owtf-backend python -c "
from owtf.proxy.proxy import set_logging_rate_limit
set_logging_rate_limit(50)
"

# Check for connection limits
docker exec -it owtf-backend netstat -an | grep 8008
```

### Debug Mode

**Enable Debug Logging**:
```bash
# Enable debug for proxy
docker exec -it owtf-backend python -c "
import logging
logger = logging.getLogger('owtf.proxy.proxy')
logger.setLevel(logging.DEBUG)
"

# Enable debug for HTTPS interceptor
docker exec -it owtf-backend python -c "
import logging
logger = logging.getLogger('owtf.proxy.https_interceptor')
logger.setLevel(logging.DEBUG)
"
```

**Verbose Testing**:
```bash
# Test with verbose output
curl -x http://localhost:8008 -v https://httpbin.org/get

# Check SSL handshake details
openssl s_client -connect localhost:8008 -proxy localhost:8008
```

## Advanced Configuration

### 1. Custom Certificate Paths

**Modify Configuration**:
```python
# In owtf/proxy/main.py
CA_CERT_PATH = "/custom/path/ca.crt"
CA_KEY_PATH = "/custom/path/ca.key"
CERT_FOLDER = "/custom/path/certs/"
```

### 2. Custom Interceptor Rules

**Create Custom Interceptor**:
```python
from owtf.proxy.interceptors.base import BaseInterceptor

class CustomInterceptor(BaseInterceptor):
    def __init__(self):
        super().__init__("Custom Interceptor", priority=500)
    
    def intercept_request(self, request):
        # Add custom logic here
        request.headers["X-Custom"] = "custom-value"
        return request
```

### 3. Environment Variables

**Set Custom Configuration**:
```bash
export OWTF_PROXY_PORT=9000
export OWTF_LOG_LEVEL=DEBUG
export OWTF_CERT_PATH=/custom/certs/
```

## Security Considerations

### 1. Production Deployment

**Access Control**:
- Implement authentication for the web interface
- Restrict proxy access to authorized users
- Use firewall rules to limit access

**Certificate Security**:
- Secure storage of CA private key
- Regular certificate rotation
- Monitor certificate expiration

### 2. Privacy and Compliance

**Data Handling**:
- All intercepted traffic is logged
- Implement log retention policies
- Ensure compliance with privacy regulations
- Inform users about traffic interception

**Audit Logging**:
- Log all administrative actions
- Monitor for suspicious activities
- Regular security reviews

## Next Steps

### 1. Explore Features

- **Interceptor System**: Learn about different interceptor types
- **Live Interceptor**: Master real-time request modification
- **API Integration**: Use the REST API for automation
- **Custom Development**: Create custom interceptors

### 2. Advanced Testing

- **Security Testing**: Test for common vulnerabilities
- **Performance Testing**: Analyze response times and bottlenecks
- **Load Testing**: Test under high traffic conditions
- **Protocol Testing**: Test various HTTP methods and protocols

### 3. Integration

- **CI/CD Integration**: Integrate with automated testing pipelines
- **Monitoring**: Set up monitoring and alerting
- **Reporting**: Generate automated security reports
- **Team Collaboration**: Share configurations and findings

## Getting Help

### 1. Documentation

- **Component Docs**: Refer to individual component documentation
- **API Reference**: Use the API reference for integration
- **Architecture Guide**: Understand the system design

### 2. Community Support

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share experiences
- **Contributions**: Contribute code and documentation

### 3. Professional Support

- **Enterprise Support**: Available for commercial deployments
- **Training**: Custom training and workshops
- **Consulting**: Professional implementation services

## Conclusion

The OWTF proxy provides a powerful platform for web application security testing and analysis. This guide covers the essential setup and basic usage to get you started quickly. As you become more familiar with the system, explore the advanced features and customization options to maximize its potential for your security testing needs.

For additional information, refer to the comprehensive documentation files in this directory and the main OWTF project documentation.
