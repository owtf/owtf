package main

import (
	"bytes"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"

	owtfconfig "github.com/owtf/owtf/internal/config"
)

func TestConfigurationCommandsAndPrecedence(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config.yaml")
	if err := os.WriteFile(path, []byte(`
apiVersion: owtf.dev/v1alpha1
kind: Config
server:
  workers: 2
  taskTimeoutSeconds: 60
proxy:
  cacheEntries: 0
`), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("OWTF_WORKERS", "3")
	t.Setenv("OWTF_PROXY_UPSTREAM", "http://operator:secret@proxy.test:8080")

	settings, err := serverConfiguration([]string{
		"--config", path, "--workers", "4", "--task-timeout", "2m",
	}, io.Discard)
	if err != nil {
		t.Fatal(err)
	}
	if settings.Server.Workers != 4 || settings.Server.TaskTimeoutSeconds != 120 || settings.Proxy.CacheEntries != 0 {
		t.Fatalf("configuration = %+v", settings)
	}

	var shown bytes.Buffer
	if err := run([]string{"config", "show", "--config", path}, &shown, io.Discard); err != nil {
		t.Fatal(err)
	}
	var decoded owtfconfig.Config
	if err := json.Unmarshal(shown.Bytes(), &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded.Server.Workers != 3 || strings.Contains(decoded.Proxy.Upstream, "operator") || strings.Contains(decoded.Proxy.Upstream, "secret") {
		t.Fatalf("shown configuration = %+v", decoded)
	}

	var validated bytes.Buffer
	if err := run([]string{"config", "validate", path}, &validated, io.Discard); err != nil {
		t.Fatal(err)
	}
	var result struct {
		Valid bool `json:"valid"`
	}
	if err := json.Unmarshal(validated.Bytes(), &result); err != nil || !result.Valid {
		t.Fatalf("validate output = %q, error = %v", validated.String(), err)
	}
}

func TestConfigurationCommandsRejectInvalidInput(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config.yaml")
	if err := os.WriteFile(path, []byte("apiVersion: owtf.dev/v1alpha1\nkind: Config\nunknown: true\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := run([]string{"config", "validate", path}, io.Discard, io.Discard); err == nil {
		t.Fatal("invalid configuration was accepted")
	}
	if _, err := serverConfiguration([]string{"--task-timeout", "500ms"}, io.Discard); err == nil {
		t.Fatal("sub-second task timeout was accepted")
	}
	if _, err := configurationPath([]string{"--config"}); err == nil {
		t.Fatal("missing configuration path was accepted")
	}
}
