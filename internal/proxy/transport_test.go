package proxy

import (
	"context"
	"encoding/binary"
	"io"
	"net"
	"net/http"
	"testing"
	"time"
)

func TestSOCKS5DialerUsesCredentialsAndDestination(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	serverErr := make(chan error, 1)
	go func() { serverErr <- serveSOCKS5Test(listener) }()

	dialer, err := NewSOCKS5Dialer(listener.Addr().String(), "operator", "secret")
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	connection, err := dialer.DialContext(ctx, "tcp", "target.example:8443")
	if err != nil {
		t.Fatal(err)
	}
	data, err := io.ReadAll(connection)
	connection.Close()
	if err != nil || string(data) != "connected" {
		t.Fatalf("tunnel data = %q, error = %v", data, err)
	}
	if err := <-serverErr; err != nil {
		t.Fatal(err)
	}
}

func TestSetUpstreamConfiguresSupportedSchemes(t *testing.T) {
	for _, value := range []string{
		"http://user:pass@127.0.0.1:8080",
		"https://127.0.0.1:8443",
		"socks5://user:pass@127.0.0.1:1080",
	} {
		transport := http.DefaultTransport.(*http.Transport).Clone()
		if err := SetUpstream(transport, value); err != nil {
			t.Fatalf("SetUpstream(%q): %v", value, err)
		}
	}
	transport := http.DefaultTransport.(*http.Transport).Clone()
	if err := SetUpstream(transport, "ftp://127.0.0.1:21"); err == nil {
		t.Fatal("unsupported upstream scheme was accepted")
	}
}

func serveSOCKS5Test(listener net.Listener) error {
	connection, err := listener.Accept()
	if err != nil {
		return err
	}
	defer connection.Close()
	header := make([]byte, 2)
	if _, err := io.ReadFull(connection, header); err != nil {
		return err
	}
	methods := make([]byte, int(header[1]))
	if _, err := io.ReadFull(connection, methods); err != nil {
		return err
	}
	if header[0] != 5 || !containsByte(methods, 2) {
		return io.ErrUnexpectedEOF
	}
	if _, err := connection.Write([]byte{5, 2}); err != nil {
		return err
	}
	credentials := make([]byte, 2)
	if _, err := io.ReadFull(connection, credentials); err != nil {
		return err
	}
	username := make([]byte, int(credentials[1]))
	if _, err := io.ReadFull(connection, username); err != nil {
		return err
	}
	passwordLength := make([]byte, 1)
	if _, err := io.ReadFull(connection, passwordLength); err != nil {
		return err
	}
	password := make([]byte, int(passwordLength[0]))
	if _, err := io.ReadFull(connection, password); err != nil {
		return err
	}
	if credentials[0] != 1 || string(username) != "operator" || string(password) != "secret" {
		return io.ErrUnexpectedEOF
	}
	if _, err := connection.Write([]byte{1, 0}); err != nil {
		return err
	}
	request := make([]byte, 5)
	if _, err := io.ReadFull(connection, request); err != nil {
		return err
	}
	if request[0] != 5 || request[1] != 1 || request[3] != 3 {
		return io.ErrUnexpectedEOF
	}
	host := make([]byte, int(request[4]))
	if _, err := io.ReadFull(connection, host); err != nil {
		return err
	}
	port := make([]byte, 2)
	if _, err := io.ReadFull(connection, port); err != nil {
		return err
	}
	if string(host) != "target.example" || binary.BigEndian.Uint16(port) != 8443 {
		return io.ErrUnexpectedEOF
	}
	if _, err := connection.Write([]byte{5, 0, 0, 1, 127, 0, 0, 1, 0, 80}); err != nil {
		return err
	}
	_, err = connection.Write([]byte("connected"))
	return err
}

func containsByte(values []byte, want byte) bool {
	for _, value := range values {
		if value == want {
			return true
		}
	}
	return false
}
