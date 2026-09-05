package plugin

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestProxyTransportRoutesLoopback(t *testing.T) {
	proxy := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.String() != "http://127.0.0.1:1/test" {
			t.Errorf("URL = %s", r.URL)
		}
		w.Write([]byte("captured"))
	}))
	defer proxy.Close()
	transport, err := NewProxyTransport(proxy.URL, "")
	if err != nil {
		t.Fatal(err)
	}
	response, err := (&http.Client{Transport: transport}).Get("http://127.0.0.1:1/test")
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	body, _ := io.ReadAll(response.Body)
	if string(body) != "captured" {
		t.Fatalf("body = %s", body)
	}
}

func TestProxyTransportMissingCAFailsClosed(t *testing.T) {
	transport, err := NewProxyTransport("http://127.0.0.1:1", t.TempDir()+"/missing.pem")
	if err != nil {
		t.Fatal(err)
	}
	_, err = (&http.Client{Transport: transport}).Get("https://example.invalid/")
	if err == nil || !strings.Contains(err.Error(), "read plugin proxy CA") {
		t.Fatalf("error = %v", err)
	}
}

func TestProxyTransportRejectsInvalidConfiguration(t *testing.T) {
	for _, address := range []string{"", "socks5://localhost:8008", "http://user:pass@localhost", "http://localhost/path", "http://localhost?target=x"} {
		if _, err := NewProxyTransport(address, ""); err == nil {
			t.Errorf("accepted %q", address)
		}
	}
}

func TestCommandProxyEnvironment(t *testing.T) {
	t.Setenv("OWTF_PLUGIN_PROXY", "http://127.0.0.1:8008")
	t.Setenv("OWTF_PLUGIN_PROXY_CA", "/data/ca.pem")
	env := strings.Join(commandEnvironment(Request{}, "/tmp/task"), "\n")
	for _, entry := range []string{"http_proxy=http://127.0.0.1:8008", "HTTPS_PROXY=http://127.0.0.1:8008", "CURL_CA_BUNDLE=/data/ca.pem"} {
		if !strings.Contains(env, entry) {
			t.Errorf("missing %s", entry)
		}
	}
}
