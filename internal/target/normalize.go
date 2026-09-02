package target

import (
	"fmt"
	"net"
	"net/url"
	"regexp"
	"strings"
)

// Normalized contains the classified and canonical form of a target value.
type Normalized struct {
	Kind     string
	Original string
	Value    string
}

var hostnamePattern = regexp.MustCompile(`^(?i:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)(?:\.(?i:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?))*\.?$`)

// Normalize accepts an HTTP(S) URL, hostname, IP address, or CIDR and rejects
// ambiguous or unsafe values before they enter a session.
func Normalize(raw string) (Normalized, error) {
	original := strings.TrimSpace(raw)
	if original == "" {
		return Normalized{}, fmt.Errorf("target is empty")
	}

	if strings.Contains(original, "://") {
		return normalizeURL(original)
	}
	if ip := net.ParseIP(original); ip != nil {
		return Normalized{Kind: "ip", Original: original, Value: ip.String()}, nil
	}
	if _, network, err := net.ParseCIDR(original); err == nil {
		return Normalized{Kind: "cidr", Original: original, Value: network.String()}, nil
	}

	hostname := strings.TrimSuffix(strings.ToLower(original), ".")
	if len(hostname) > 253 || !hostnamePattern.MatchString(hostname) {
		return Normalized{}, fmt.Errorf("target must be an HTTP(S) URL, hostname, IP, or CIDR")
	}
	return Normalized{Kind: "hostname", Original: original, Value: hostname}, nil
}

func normalizeURL(raw string) (Normalized, error) {
	u, err := url.Parse(raw)
	if err != nil || u.Host == "" {
		return Normalized{}, fmt.Errorf("invalid URL")
	}
	u.Scheme = strings.ToLower(u.Scheme)
	if u.Scheme != "http" && u.Scheme != "https" {
		return Normalized{}, fmt.Errorf("URL scheme must be http or https")
	}
	if u.User != nil {
		return Normalized{}, fmt.Errorf("credentials are not allowed in target URLs")
	}

	host := strings.ToLower(u.Hostname())
	port := u.Port()
	if (u.Scheme == "http" && port == "80") || (u.Scheme == "https" && port == "443") {
		port = ""
	}
	if port != "" {
		u.Host = net.JoinHostPort(host, port)
	} else {
		u.Host = host
	}
	if u.Path == "" {
		u.Path = "/"
	}
	u.Fragment = ""

	return Normalized{Kind: "url", Original: raw, Value: u.String()}, nil
}
