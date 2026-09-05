package api

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestProxyBoundary(t *testing.T) {
	var calls int
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		if r.Header.Get("Cookie") != "" || r.Header.Get("Authorization") != "" {
			t.Error("forwarded browser credentials")
		}
		if r.URL.Path != "/api/v2/interception" || r.URL.Query().Get("phase") != "request" {
			t.Errorf("wrong route: %s", r.URL)
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusConflict)
		_, _ = w.Write([]byte(`{"error":"pending"}`))
	}))
	defer upstream.Close()
	handler := proxyAPI(strings.TrimPrefix(upstream.URL, "http://"))
	r := httptest.NewRequest("PUT", "/api/v2/proxy/interception?phase=request", strings.NewReader(`{}`))
	r.Header.Set("Cookie", "session=private")
	r.Header.Set("Authorization", "Bearer private")
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, r)
	if w.Code != 409 || !strings.Contains(w.Body.String(), "pending") {
		t.Fatalf("forward: %d %s", w.Code, w.Body)
	}
	r.Header.Set("Origin", "https://untrusted.example")
	w = httptest.NewRecorder()
	handler.ServeHTTP(w, r)
	if w.Code != 403 || calls != 1 {
		t.Fatalf("cross-site command: %d calls=%d", w.Code, calls)
	}
	w = httptest.NewRecorder()
	handler.ServeHTTP(w, httptest.NewRequest("POST", "/api/v2/proxy/arbitrary", nil))
	if w.Code != 404 || calls != 1 {
		t.Fatal("unknown route forwarded")
	}
}

func TestProxyUnavailableAndRedirect(t *testing.T) {
	for _, address := range []string{"", "proxy.example:8010", "192.0.2.1:8010"} {
		w := httptest.NewRecorder()
		proxyAPI(address).ServeHTTP(w, httptest.NewRequest("GET", "/api/v2/proxy/health", nil))
		if w.Code != 503 {
			t.Fatalf("%s: %d", address, w.Code)
		}
	}
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "http://example.com", http.StatusFound)
	}))
	defer upstream.Close()
	w := httptest.NewRecorder()
	proxyAPI(strings.TrimPrefix(upstream.URL, "http://")).ServeHTTP(w, httptest.NewRequest("GET", "/api/v2/proxy/health", nil))
	if w.Code != 302 || w.Header().Get("Location") != "" {
		t.Fatal("redirect followed or exposed")
	}
}
