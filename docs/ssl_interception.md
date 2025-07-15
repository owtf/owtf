# SSL Interception in OWTF Proxy

OWTF now supports full SSL/TLS interception (Man-in-the-Middle) for HTTPS traffic. This allows the proxy to decrypt and inspect encrypted traffic between clients and servers.

## How It Works

The SSL interception process works as follows:

1. **Client Connection**: When a client makes a CONNECT request for an HTTPS site, the proxy accepts the connection
2. **SSL Termination**: The proxy terminates the SSL connection from the client using a dynamically generated certificate
3. **Upstream Connection**: The proxy establishes a new SSL connection to the upstream server
4. **Traffic Forwarding**: Decrypted traffic is forwarded bidirectionally between the two SSL connections

## Setup

### 1. Install Dependencies

Make sure you have the required dependencies:

```bash
pip install pyOpenSSL
```

### 2. Generate CA Certificate

The installation script automatically generates a Certificate Authority (CA) certificate:

```bash
./scripts/install.sh
```

This creates:
- `~/.owtf/proxy/certs/ca.crt` - CA certificate
- `~/.owtf/proxy/certs/ca.key` - CA private key
- `~/.owtf/proxy/certs/ca_pass.txt` - CA password

### 3. Trust the CA Certificate

**Important**: You must add the CA certificate to your browser's trusted certificate store:

1. Open your browser's certificate settings
2. Import `~/.owtf/proxy/certs/ca.crt` as a trusted root CA
3. Restart your browser

## Usage

### Starting the Proxy with SSL Interception

The proxy automatically enables SSL interception when started:

```bash
python -m owtf
```

The proxy will run on `0.0.0.0:8008` by default.

### Configuring Your Browser

Configure your browser to use the OWTF proxy:

- **Proxy Address**: `127.0.0.1`
- **Proxy Port**: `8008`
- **Protocol**: HTTP

### Testing SSL Interception

1. Start the OWTF proxy
2. Configure your browser to use the proxy
3. Visit any HTTPS website
4. Check the browser's certificate information - it should show the OWTF CA as the issuer

## Certificate Management

### Dynamic Certificate Generation

The proxy automatically generates certificates for each domain:

- **Regular domains**: `example.com` → certificate for `example.com`
- **Subdomains with many dots**: `sub1.sub2.sub3.example.com` → wildcard certificate for `*.sub3.example.com`

### Certificate Storage

Certificates are stored in `~/.owtf/proxy/certs/` with the following naming convention:
- Certificate: `domain_name.crt`
- Private key: `domain_name.key`

## Security Considerations

### Certificate Trust

- The CA certificate must be trusted by your browser
- Without trust, browsers will show security warnings
- This is normal behavior for SSL interception tools

### Privacy

- All HTTPS traffic is decrypted and can be inspected
- Use this feature responsibly and only on systems you control
- Never use on production systems without proper authorization

### Limitations

- Some applications may use certificate pinning and reject the proxy certificates
- Mobile apps and some desktop applications may not respect system proxy settings
- WebSocket connections (WSS) are handled separately

## Troubleshooting

### Certificate Errors

If you see certificate errors:

1. Verify the CA certificate is properly imported
2. Check that the certificate is trusted as a root CA
3. Restart your browser after importing the certificate

### Connection Issues

If connections fail:

1. Check that the proxy is running on the correct port
2. Verify firewall settings allow the connection
3. Check the proxy logs for error messages

### Performance

SSL interception adds some overhead:

- Certificate generation for new domains
- SSL handshake processing
- Memory usage for certificate storage

## Configuration

### Proxy Settings

You can modify the proxy settings in `owtf/settings.py`:

```python
# Proxy configuration
INBOUND_PROXY_IP = "0.0.0.0"
INBOUND_PROXY_PORT = 8008
CA_CERT = os.path.join(OWTF_CONF, "proxy", "certs", "ca.crt")
CA_KEY = os.path.join(OWTF_CONF, "proxy", "certs", "ca.key")
CERTS_FOLDER = os.path.join(OWTF_CONF, "proxy", "certs")
```

### Outbound Proxy

The proxy can also use an outbound proxy for upstream connections:

```python
USE_OUTBOUND_PROXY = True
OUTBOUND_PROXY_IP = "proxy.example.com"
OUTBOUND_PROXY_PORT = 8080
```

## API Integration

The SSL interception functionality is integrated into the OWTF API and can be used programmatically:

```python
from owtf.proxy.main import start_proxy

# Start the proxy with SSL interception
start_proxy()
```

## Logging

SSL interception events are logged with the following information:

- SSL handshake success/failure
- Certificate generation
- Connection establishment
- Error conditions

Check the proxy logs for detailed information about SSL interception activities. 