package api

import (
	"net/http/httptest"
	"strings"
	"testing"

	owtfconfig "github.com/owtf/owtf/internal/config"
)

func TestRuntimeConfig(t *testing.T) {
	config := owtfconfig.Default()
	config.Proxy.Upstream = "http://operator:secret@localhost:8080"
	handler := New(Config{RuntimeConfig: &config})
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, httptest.NewRequest("GET", "/api/v2/config", nil))
	if response.Code != 200 || strings.Contains(response.Body.String(), "secret") || !strings.Contains(response.Body.String(), "redacted") {
		t.Fatalf("config: %d %s", response.Code, response.Body.String())
	}
}

func TestValidateConfig(t *testing.T) {
	handler := New(Config{})
	for _, test := range []struct {
		body   string
		status int
	}{
		{`{"yaml":"apiVersion: owtf.dev/v1alpha1\nkind: Config\n"}`, 200},
		{`{"yaml":"apiVersion: owtf.dev/v1alpha1\nkind: Config\nunknown: true\n"}`, 400},
		{`{"yaml":"apiVersion: owtf.dev/v1alpha1\nkind: Config\n---\nkind: Config"}`, 400},
		{`{"yaml":""}`, 400},
	} {
		response := httptest.NewRecorder()
		handler.ServeHTTP(response, httptest.NewRequest("POST", "/api/v2/config/validate", strings.NewReader(test.body)))
		if response.Code != test.status {
			t.Errorf("%s: %d %s", test.body, response.Code, response.Body.String())
		}
	}
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, httptest.NewRequest("GET", "/api/v2/config", nil))
	if response.Code != 503 {
		t.Fatalf("missing config: %d", response.Code)
	}
}
