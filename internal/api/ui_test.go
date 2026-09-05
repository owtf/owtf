package api

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestBackendDoesNotServeUI(t *testing.T) {
	handler := New(Config{})
	for _, path := range []string{"/", "/targets/example", "/work", "/assets/app.js"} {
		response := httptest.NewRecorder()
		handler.ServeHTTP(response, httptest.NewRequest(http.MethodGet, path, nil))
		if response.Code != http.StatusNotFound {
			t.Fatalf("%s: got %d, want 404", path, response.Code)
		}
	}
}
