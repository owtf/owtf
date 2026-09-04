package api

import (
	"net/http/httptest"
	"regexp"
	"strings"
	"testing"
)

// The committed bundle keeps plain Go builds usable without a Node installation.
// Check every entry-point asset after frontend rebuilds.
func TestEmbeddedUIAssets(t *testing.T) {
	data, err := uiFiles.ReadFile("ui/index.html")
	if err != nil {
		t.Fatal(err)
	}
	assets := regexp.MustCompile(`(?:src|href)="(/assets/[^\"]+)"`).FindAllStringSubmatch(string(data), -1)
	if len(assets) < 2 {
		t.Fatal("missing built script and stylesheet")
	}
	for _, asset := range assets {
		if _, err := uiFiles.ReadFile("ui" + asset[1]); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := uiFiles.ReadFile("ui/assets/InterVariable.woff2"); err != nil {
		t.Fatal(err)
	}
}

func TestUIRoutes(t *testing.T) {
	server := &Server{}
	for _, path := range []string{"/", "/work", "/workers", "/transactions", "/settings", "/help", "/targets/test"} {
		response := httptest.NewRecorder()
		server.app(response, httptest.NewRequest("GET", path, nil))
		if response.Code != 200 || !strings.Contains(response.Body.String(), `id="root"`) {
			t.Fatalf("%s: %d", path, response.Code)
		}
	}
	for _, path := range []string{"/login", "/api/missing", "/unknown"} {
		response := httptest.NewRecorder()
		server.app(response, httptest.NewRequest("GET", path, nil))
		if response.Code != 404 {
			t.Fatalf("%s: %d", path, response.Code)
		}
	}
}
