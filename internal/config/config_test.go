package config

import (
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func TestLoadMergesDefaultsAndRejectsUnknownFields(t *testing.T) {
	path := writeConfig(t, `
apiVersion: owtf.dev/v1alpha1
kind: Config
server:
  workers: 3
proxy:
  cacheEntries: 0
`)
	loaded, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}
	if loaded.Server.Workers != 3 || loaded.Server.Address != ":8009" || loaded.Proxy.CacheEntries != 0 {
		t.Fatalf("configuration = %+v", loaded)
	}

	unknown := writeConfig(t, `
apiVersion: owtf.dev/v1alpha1
kind: Config
server:
  mystery: true
`)
	if _, err := Load(unknown); err == nil || !strings.Contains(err.Error(), "field mystery") {
		t.Fatalf("unknown field error = %v", err)
	}
}

func TestLoadRejectsInvalidDocumentsAndStoredCredentials(t *testing.T) {
	tests := []struct {
		name string
		text string
		want string
	}{
		{"missing header", "server:\n  workers: 1\n", "requires apiVersion and kind"},
		{"wrong version", "apiVersion: old\nkind: Config\n", "unsupported apiVersion"},
		{"trailing document", "apiVersion: owtf.dev/v1alpha1\nkind: Config\n---\n{}\n", "multiple YAML documents"},
		{"stored credentials", "apiVersion: owtf.dev/v1alpha1\nkind: Config\nproxy:\n  upstream: http://user:secret@proxy.test:8080\n", "credentials must come from the environment"},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			_, err := Load(writeConfig(t, test.text))
			if err == nil || !strings.Contains(err.Error(), test.want) {
				t.Fatalf("Load() error = %v, want %q", err, test.want)
			}
		})
	}
}

func TestLoadOptionalUsesDefaultsOnlyForMissingFile(t *testing.T) {
	loaded, err := LoadOptional(filepath.Join(t.TempDir(), "missing.yaml"))
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(loaded, Default()) {
		t.Fatalf("configuration = %+v", loaded)
	}
}

func TestEnvironmentOverlayIsAtomicAndRedacted(t *testing.T) {
	loaded := Default()
	values := map[string]string{
		"OWTF_WORKERS":                 "4",
		"OWTF_TASK_TIMEOUT":            "90",
		"OWTF_PROXY_CACHE_ENTRIES":     "0",
		"OWTF_PROXY_TARGET_HOSTS":      "example.test, api.example.test",
		"OWTF_PROXY_INSECURE_UPSTREAM": "true",
		"OWTF_PROXY_UPSTREAM":          "http://operator:secret@proxy.test:8080",
		"OWTF_PROXY_COOKIE_BLACKLIST":  "",
		"OWTF_PROXY_COOKIE_WHITELIST":  "session",
		"OWTF_PROXY_MAX_TRANSACTIONS":  "250",
		"OWTF_PROXY_MAX_BODY":          "2048",
		"OWTF_PROXY_CACHE_MAX_BODY":    "1024",
		"OWTF_PROXY_HTTP_AUTH_FILE":    "auth.json",
		"OWTF_PROXY_INTERCEPTOR_FILE":  "interceptors.json",
	}
	lookup := func(name string) (string, bool) { value, ok := values[name]; return value, ok }
	if err := loaded.ApplyEnvironment(lookup); err != nil {
		t.Fatal(err)
	}
	if loaded.Server.Workers != 4 || loaded.Server.TaskTimeoutSeconds != 90 || loaded.Proxy.CacheEntries != 0 ||
		len(loaded.Proxy.TargetHosts) != 2 || !loaded.Proxy.InsecureUpstream || len(loaded.Proxy.CookieBlacklist) != 0 {
		t.Fatalf("configuration = %+v", loaded)
	}
	if strings.Contains(loaded.Redacted().Proxy.Upstream, "operator") || strings.Contains(loaded.Redacted().Proxy.Upstream, "secret") {
		t.Fatalf("redacted upstream = %q", loaded.Redacted().Proxy.Upstream)
	}

	original := loaded
	values = map[string]string{"OWTF_WORKERS": "many"}
	if err := loaded.ApplyEnvironment(lookup); err == nil {
		t.Fatal("invalid environment was accepted")
	}
	if loaded.Server.Workers != original.Server.Workers {
		t.Fatal("invalid environment partially changed configuration")
	}
}

func TestValidateBounds(t *testing.T) {
	loaded := Default()
	loaded.Server.Workers = 65
	if err := loaded.Validate(); err == nil || !strings.Contains(err.Error(), "server.workers") {
		t.Fatalf("Validate() error = %v", err)
	}
	loaded = Default()
	loaded.Proxy.Attempts = 0
	if err := loaded.Validate(); err == nil || !strings.Contains(err.Error(), "proxy.attempts") {
		t.Fatalf("Validate() error = %v", err)
	}
}

func writeConfig(t *testing.T, text string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "config.yaml")
	if err := os.WriteFile(path, []byte(strings.TrimSpace(text)+"\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	return path
}
