package proxy

import (
	"crypto/tls"
	"crypto/x509"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/owtf/owtf/internal/har"
)

func TestProxyCapturesHTTPTransaction(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		body, _ := io.ReadAll(request.Body)
		writer.Header().Add("X-Upstream", "one")
		writer.Header().Add("X-Upstream", "two")
		writer.WriteHeader(http.StatusCreated)
		_, _ = writer.Write(append([]byte("received:"), body...))
	}))
	defer upstream.Close()

	recorder := NewRecorder(10)
	proxyServer := newTestProxyServer(t, recorder, []string{hostFromURL(t, upstream.URL)}, nil)
	defer proxyServer.Close()
	client := proxyClient(t, proxyServer.URL, nil)
	request, err := http.NewRequest(http.MethodPost, upstream.URL+"/submit", strings.NewReader("payload"))
	if err != nil {
		t.Fatal(err)
	}
	request.Header.Set("Content-Type", "text/plain")
	response, err := client.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(response.Body)
	response.Body.Close()
	if response.StatusCode != http.StatusCreated || string(body) != "received:payload" {
		t.Fatalf("unexpected proxy response: status=%d body=%q", response.StatusCode, body)
	}
	transaction := waitForTransaction(t, recorder)
	if transaction.Method != http.MethodPost || transaction.URL != upstream.URL+"/submit" || string(transaction.RequestBody) != "payload" {
		t.Fatalf("unexpected request capture: %+v", transaction)
	}
	if transaction.StatusCode != http.StatusCreated || string(transaction.ResponseBody) != "received:payload" {
		t.Fatalf("unexpected response capture: %+v", transaction)
	}
	if !strings.Contains(transaction.ResponseHeaders, `"X-Upstream":["one","two"]`) {
		t.Fatalf("duplicate response headers were not retained: %s", transaction.ResponseHeaders)
	}
}

func TestProxyInterceptsHTTPSAndWritesImportableHAR(t *testing.T) {
	upstream := httptest.NewTLSServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		writer.Header().Set("Content-Type", "application/octet-stream")
		_, _ = writer.Write([]byte{0, 1, 2, 3})
	}))
	defer upstream.Close()

	directory := t.TempDir()
	authority, err := LoadOrCreateAuthority(filepath.Join(directory, "ca.crt"), filepath.Join(directory, "ca.key"))
	if err != nil {
		t.Fatal(err)
	}
	recorder := NewRecorder(10)
	upstreamTransport := upstream.Client().Transport.(*http.Transport).Clone()
	proxyHandler, err := New(Config{
		Authority: authority, Recorder: recorder, Transport: upstreamTransport,
		AllowedHosts: []string{hostFromURL(t, upstream.URL)},
	})
	if err != nil {
		t.Fatal(err)
	}
	proxyServer := httptest.NewServer(proxyHandler)
	defer proxyServer.Close()

	roots := x509.NewCertPool()
	if !roots.AppendCertsFromPEM(authority.CertificatePEM()) {
		t.Fatal("could not trust test proxy CA")
	}
	client := proxyClient(t, proxyServer.URL, &tls.Config{RootCAs: roots, MinVersion: tls.VersionTLS12})
	response, err := client.Get(upstream.URL + "/binary")
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(response.Body)
	response.Body.Close()
	if string(body) != string([]byte{0, 1, 2, 3}) {
		t.Fatalf("HTTPS response changed: %v", body)
	}
	transaction := waitForTransaction(t, recorder)
	if transaction.URL != upstream.URL+"/binary" || string(transaction.ResponseBody) != string(body) {
		t.Fatalf("unexpected HTTPS capture: %+v", transaction)
	}
	harPath := filepath.Join(directory, "capture.har")
	if err := recorder.WriteHAR(harPath); err != nil {
		t.Fatal(err)
	}
	file, err := os.Open(harPath)
	if err != nil {
		t.Fatal(err)
	}
	parsed, err := har.Parse(file)
	file.Close()
	if err != nil || len(parsed) != 1 || string(parsed[0].ResponseBody) != string(body) {
		t.Fatalf("proxy HAR did not round trip: transactions=%+v error=%v", parsed, err)
	}
}

func TestProxyRejectsHostOutsideScope(t *testing.T) {
	recorder := NewRecorder(10)
	proxyServer := newTestProxyServer(t, recorder, []string{"allowed.test"}, nil)
	defer proxyServer.Close()
	client := proxyClient(t, proxyServer.URL, nil)
	response, err := client.Get("http://127.0.0.1:1/outside")
	if err != nil {
		t.Fatal(err)
	}
	response.Body.Close()
	if response.StatusCode != http.StatusForbidden || len(recorder.Transactions()) != 0 {
		t.Fatalf("outside host was not rejected: status=%d transactions=%d", response.StatusCode, len(recorder.Transactions()))
	}
}

func TestProxyAppliesInterceptorsAndRejectsScopeEscape(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		body, _ := io.ReadAll(request.Body)
		writer.Header().Set("Content-Type", "text/plain")
		_, _ = writer.Write([]byte(request.URL.Path + ":" + request.Header.Get("X-Request") + ":" + string(body)))
	}))
	defer upstream.Close()
	host := hostFromURL(t, upstream.URL)
	interceptors, err := NewInterceptors([]InterceptorRule{
		{
			Name: "request", Phase: "request",
			Action: InterceptorAction{
				SetHeaders: map[string]string{"X-Request": "modified"},
				BodyAppend: "+request", RewriteURL: &TextReplacement{Pattern: `/before`, Replacement: `/after`},
			},
		},
		{
			Name: "response", Phase: "response", Match: InterceptorMatch{ContentTypes: []string{"text/plain"}},
			Action: InterceptorAction{BodyAppend: "+response"},
		},
	}, 1024)
	if err != nil {
		t.Fatal(err)
	}
	recorder := NewRecorder(10)
	proxyServer := newTestProxyServerWithInterceptors(t, recorder, []string{host}, nil, interceptors)
	defer proxyServer.Close()
	client := proxyClient(t, proxyServer.URL, nil)
	request, _ := http.NewRequest(http.MethodPost, upstream.URL+"/before", strings.NewReader("body"))
	response, err := client.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(response.Body)
	response.Body.Close()
	if string(body) != "/after:modified:body+request+response" {
		t.Fatalf("intercepted response = %q", body)
	}

	escape, _ := NewInterceptors([]InterceptorRule{{
		Name: "escape", Phase: "request",
		Action: InterceptorAction{RewriteURL: &TextReplacement{Pattern: `^.*?/before$`, Replacement: "http://outside.test/"}},
	}}, 1024)
	escapeProxy := newTestProxyServerWithInterceptors(t, NewRecorder(10), []string{host}, nil, escape)
	defer escapeProxy.Close()
	escapeClient := proxyClient(t, escapeProxy.URL, nil)
	escapeResponse, err := escapeClient.Get(upstream.URL + "/before")
	if err != nil {
		t.Fatal(err)
	}
	escapeResponse.Body.Close()
	if escapeResponse.StatusCode != http.StatusForbidden {
		t.Fatalf("scope escape status = %d", escapeResponse.StatusCode)
	}
}

func TestProxyDoesNotInterceptUpgradeResponse(t *testing.T) {
	interceptors, err := NewInterceptors([]InterceptorRule{{
		Name: "response", Phase: "response",
		Action: InterceptorAction{SetHeaders: map[string]string{"X-Intercepted": "true"}, BodyAppend: "blocked"},
	}}, 1024)
	if err != nil {
		t.Fatal(err)
	}
	transport := roundTripperFunc(func(request *http.Request) (*http.Response, error) {
		return &http.Response{
			StatusCode: http.StatusSwitchingProtocols,
			Status:     "101 Switching Protocols",
			Proto:      "HTTP/1.1",
			ProtoMajor: 1,
			ProtoMinor: 1,
			Header:     http.Header{"Connection": {"Upgrade"}, "Upgrade": {"websocket"}},
			Body:       io.NopCloser(strings.NewReader("")),
			Request:    request,
		}, nil
	})
	directory := t.TempDir()
	authority, err := LoadOrCreateAuthority(filepath.Join(directory, "ca.crt"), filepath.Join(directory, "ca.key"))
	if err != nil {
		t.Fatal(err)
	}
	transactions := NewRecorder(10)
	handler, err := New(Config{
		Authority: authority, Recorder: transactions, Transport: transport,
		AllowedHosts: []string{"example.test"}, Interceptors: interceptors,
	})
	if err != nil {
		t.Fatal(err)
	}
	request := httptest.NewRequest(http.MethodGet, "http://example.test/socket", nil)
	request.Header.Set("Connection", "Upgrade")
	request.Header.Set("Upgrade", "websocket")
	handler.ServeHTTP(httptest.NewRecorder(), request)

	captured := transactions.Transactions()
	if len(captured) != 1 {
		t.Fatalf("captured %d upgrade transactions", len(captured))
	}
	if strings.Contains(captured[0].ResponseHeaders, "X-Intercepted") {
		t.Fatalf("upgrade response was intercepted: %s", captured[0].ResponseHeaders)
	}
}

func newTestProxyServer(t *testing.T, recorder *Recorder, hosts []string, transport http.RoundTripper) *httptest.Server {
	return newTestProxyServerWithInterceptors(t, recorder, hosts, transport, nil)
}

func newTestProxyServerWithInterceptors(t *testing.T, recorder *Recorder, hosts []string, transport http.RoundTripper, interceptors *Interceptors) *httptest.Server {
	t.Helper()
	directory := t.TempDir()
	authority, err := LoadOrCreateAuthority(filepath.Join(directory, "ca.crt"), filepath.Join(directory, "ca.key"))
	if err != nil {
		t.Fatal(err)
	}
	handler, err := New(Config{
		Authority: authority, Recorder: recorder, AllowedHosts: hosts,
		Transport: transport, Interceptors: interceptors,
	})
	if err != nil {
		t.Fatal(err)
	}
	return httptest.NewServer(handler)
}

func proxyClient(t *testing.T, address string, tlsConfig *tls.Config) *http.Client {
	t.Helper()
	proxyURL, err := url.Parse(address)
	if err != nil {
		t.Fatal(err)
	}
	return &http.Client{
		Timeout:   5 * time.Second,
		Transport: &http.Transport{Proxy: http.ProxyURL(proxyURL), TLSClientConfig: tlsConfig},
	}
}

func hostFromURL(t *testing.T, value string) string {
	t.Helper()
	parsed, err := url.Parse(value)
	if err != nil {
		t.Fatal(err)
	}
	return parsed.Hostname()
}

func waitForTransaction(t *testing.T, recorder *Recorder) har.Transaction {
	t.Helper()
	deadline := time.Now().Add(time.Second)
	for {
		transactions := recorder.Transactions()
		if len(transactions) > 0 {
			return transactions[0]
		}
		if time.Now().After(deadline) {
			t.Fatal("proxy transaction was not recorded")
		}
		time.Sleep(5 * time.Millisecond)
	}
}
