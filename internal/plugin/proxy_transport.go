package plugin

import (
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"sync"
)

// ProxyTransport routes collector requests explicitly, including loopback URLs.
// The CA is loaded lazily because Compose starts the proxy after the API.
// Missing or invalid trust material fails the request; it never disables TLS verification.
type ProxyTransport struct {
	mu        sync.Mutex
	transport *http.Transport
	caFile    string
	trusted   bool
}

// NewProxyTransport accepts an operator-configured HTTP proxy, not target input.
func NewProxyTransport(address, caFile string) (*ProxyTransport, error) {
	u, err := url.Parse(address)
	if err != nil || u.Scheme != "http" || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || (u.Path != "" && u.Path != "/") {
		return nil, fmt.Errorf("plugin proxy must be an HTTP URL without credentials, path, query or fragment")
	}
	t := http.DefaultTransport.(*http.Transport).Clone()
	t.Proxy = http.ProxyURL(u)
	return &ProxyTransport{transport: t, caFile: caFile}, nil
}

func (p *ProxyTransport) RoundTrip(request *http.Request) (*http.Response, error) {
	p.mu.Lock()
	if request.URL.Scheme == "https" && !p.trusted && p.caFile != "" {
		pem, err := os.ReadFile(p.caFile)
		if err != nil {
			p.mu.Unlock()
			return nil, fmt.Errorf("read plugin proxy CA: %w", err)
		}
		roots, err := x509.SystemCertPool()
		if err != nil {
			p.mu.Unlock()
			return nil, fmt.Errorf("load system trust: %w", err)
		}
		if !roots.AppendCertsFromPEM(pem) {
			p.mu.Unlock()
			return nil, fmt.Errorf("plugin proxy CA contains no certificates")
		}
		// Clone rather than mutate a transport already serving concurrent HTTP requests.
		t := p.transport.Clone()
		t.TLSClientConfig = &tls.Config{RootCAs: roots, MinVersion: tls.VersionTLS12}
		p.transport.CloseIdleConnections()
		p.transport = t
		p.trusted = true
	}
	t := p.transport
	p.mu.Unlock()
	return t.RoundTrip(request)
}
