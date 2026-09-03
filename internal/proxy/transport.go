package proxy

import (
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

// SetUpstream configures an HTTP transport to use an HTTP, HTTPS, or SOCKS5
// proxy. Credentials belong in the upstream URL user information.
func SetUpstream(transport *http.Transport, value string) error {
	if transport == nil {
		return errors.New("HTTP transport is required")
	}
	upstream, err := url.Parse(value)
	if err != nil || upstream.Host == "" {
		return fmt.Errorf("invalid upstream proxy URL %q", value)
	}
	if (upstream.Path != "" && upstream.Path != "/") || upstream.RawQuery != "" || upstream.Fragment != "" {
		return fmt.Errorf("upstream proxy URL cannot contain a path, query, or fragment")
	}
	switch strings.ToLower(upstream.Scheme) {
	case "http", "https":
		transport.Proxy = http.ProxyURL(upstream)
	case "socks5", "socks5h":
		username, password := "", ""
		if upstream.User != nil {
			username = upstream.User.Username()
			password, _ = upstream.User.Password()
		}
		dialer, err := NewSOCKS5Dialer(upstream.Host, username, password)
		if err != nil {
			return err
		}
		transport.Proxy = nil
		transport.DialContext = dialer.DialContext
	default:
		return fmt.Errorf("unsupported upstream proxy scheme %q", upstream.Scheme)
	}
	return nil
}

// SOCKS5Dialer establishes TCP connections through a SOCKS5 proxy.
type SOCKS5Dialer struct {
	address  string
	username string
	password string
	dialer   net.Dialer
}

// NewSOCKS5Dialer creates a dialer with optional RFC 1929 credentials.
func NewSOCKS5Dialer(address, username, password string) (*SOCKS5Dialer, error) {
	if _, _, err := net.SplitHostPort(address); err != nil {
		return nil, fmt.Errorf("invalid SOCKS5 address %q: %w", address, err)
	}
	if len(username) > 255 || len(password) > 255 {
		return nil, errors.New("SOCKS5 credentials cannot exceed 255 bytes")
	}
	if username == "" && password != "" {
		return nil, errors.New("SOCKS5 password requires a username")
	}
	return &SOCKS5Dialer{address: address, username: username, password: password}, nil
}

// DialContext implements the function expected by http.Transport.
func (d *SOCKS5Dialer) DialContext(ctx context.Context, network, address string) (net.Conn, error) {
	if network != "tcp" && network != "tcp4" && network != "tcp6" {
		return nil, fmt.Errorf("SOCKS5 does not support network %q", network)
	}
	connection, err := d.dialer.DialContext(ctx, "tcp", d.address)
	if err != nil {
		return nil, fmt.Errorf("connect to SOCKS5 proxy: %w", err)
	}
	success := false
	stopCancellation := context.AfterFunc(ctx, func() { _ = connection.SetDeadline(time.Now()) })
	defer stopCancellation()
	defer func() {
		if !success {
			connection.Close()
		}
	}()

	deadline := time.Now().Add(10 * time.Second)
	if contextDeadline, ok := ctx.Deadline(); ok && contextDeadline.Before(deadline) {
		deadline = contextDeadline
	}
	if err := connection.SetDeadline(deadline); err != nil {
		return nil, err
	}
	if err := d.negotiate(connection); err != nil {
		return nil, contextError(ctx, err)
	}
	if err := requestSOCKSConnection(connection, address); err != nil {
		return nil, contextError(ctx, err)
	}
	if !stopCancellation() {
		return nil, ctx.Err()
	}
	if err := connection.SetDeadline(time.Time{}); err != nil {
		return nil, err
	}
	success = true
	return connection, nil
}

func (d *SOCKS5Dialer) negotiate(connection net.Conn) error {
	methods := []byte{0}
	if d.username != "" {
		methods = append(methods, 2)
	}
	request := append([]byte{5, byte(len(methods))}, methods...)
	if err := writeAll(connection, request); err != nil {
		return fmt.Errorf("write SOCKS5 greeting: %w", err)
	}
	var response [2]byte
	if _, err := io.ReadFull(connection, response[:]); err != nil {
		return fmt.Errorf("read SOCKS5 greeting: %w", err)
	}
	if response[0] != 5 {
		return fmt.Errorf("SOCKS5 proxy selected invalid version %d", response[0])
	}
	switch response[1] {
	case 0:
		return nil
	case 2:
		if d.username == "" {
			return errors.New("SOCKS5 proxy requires credentials")
		}
		return d.authenticate(connection)
	case 255:
		return errors.New("SOCKS5 proxy rejected all authentication methods")
	default:
		return fmt.Errorf("SOCKS5 proxy selected unsupported authentication method %d", response[1])
	}
}

func (d *SOCKS5Dialer) authenticate(connection net.Conn) error {
	request := []byte{1, byte(len(d.username))}
	request = append(request, d.username...)
	request = append(request, byte(len(d.password)))
	request = append(request, d.password...)
	if err := writeAll(connection, request); err != nil {
		return fmt.Errorf("write SOCKS5 credentials: %w", err)
	}
	var response [2]byte
	if _, err := io.ReadFull(connection, response[:]); err != nil {
		return fmt.Errorf("read SOCKS5 credentials response: %w", err)
	}
	if response[0] != 1 || response[1] != 0 {
		return errors.New("SOCKS5 credentials were rejected")
	}
	return nil
}

func requestSOCKSConnection(connection net.Conn, address string) error {
	host, portText, err := net.SplitHostPort(address)
	if err != nil {
		return fmt.Errorf("invalid SOCKS5 destination %q: %w", address, err)
	}
	port, err := strconv.ParseUint(portText, 10, 16)
	if err != nil || port == 0 {
		return fmt.Errorf("invalid SOCKS5 destination port %q", portText)
	}
	request := []byte{5, 1, 0}
	switch address := net.ParseIP(host); {
	case address == nil:
		if len(host) == 0 || len(host) > 255 {
			return errors.New("SOCKS5 destination host must contain 1 to 255 bytes")
		}
		request = append(request, 3, byte(len(host)))
		request = append(request, host...)
	case address.To4() != nil:
		request = append(request, 1)
		request = append(request, address.To4()...)
	default:
		request = append(request, 4)
		request = append(request, address.To16()...)
	}
	request = binary.BigEndian.AppendUint16(request, uint16(port))
	if err := writeAll(connection, request); err != nil {
		return fmt.Errorf("write SOCKS5 connection request: %w", err)
	}

	header := make([]byte, 4)
	if _, err := io.ReadFull(connection, header); err != nil {
		return fmt.Errorf("read SOCKS5 connection response: %w", err)
	}
	if header[0] != 5 || header[2] != 0 {
		return errors.New("SOCKS5 proxy returned an invalid response")
	}
	if header[1] != 0 {
		return fmt.Errorf("SOCKS5 proxy refused the connection: %s", socksReply(header[1]))
	}
	if err := discardSOCKSAddress(connection, header[3]); err != nil {
		return err
	}
	return nil
}

func discardSOCKSAddress(connection net.Conn, addressType byte) error {
	size := 0
	switch addressType {
	case 1:
		size = 4
	case 3:
		var length [1]byte
		if _, err := io.ReadFull(connection, length[:]); err != nil {
			return fmt.Errorf("read SOCKS5 bound address length: %w", err)
		}
		size = int(length[0])
	case 4:
		size = 16
	default:
		return fmt.Errorf("SOCKS5 proxy returned unknown address type %d", addressType)
	}
	if _, err := io.CopyN(io.Discard, connection, int64(size+2)); err != nil {
		return fmt.Errorf("read SOCKS5 bound address: %w", err)
	}
	return nil
}

func socksReply(code byte) string {
	switch code {
	case 1:
		return "general failure"
	case 2:
		return "connection not allowed"
	case 3:
		return "network unreachable"
	case 4:
		return "host unreachable"
	case 5:
		return "connection refused"
	case 6:
		return "TTL expired"
	case 7:
		return "command not supported"
	case 8:
		return "address type not supported"
	}
	return fmt.Sprintf("error %d", code)
}

func writeAll(writer io.Writer, data []byte) error {
	for len(data) > 0 {
		written, err := writer.Write(data)
		if err != nil {
			return err
		}
		if written == 0 {
			return io.ErrShortWrite
		}
		data = data[written:]
	}
	return nil
}

func contextError(ctx context.Context, err error) error {
	if ctx.Err() != nil {
		return ctx.Err()
	}
	return err
}
