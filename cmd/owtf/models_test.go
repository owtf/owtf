package main

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestModelsListIsOffline(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config.yaml")
	err := os.WriteFile(path, []byte(`apiVersion: owtf.dev/v1alpha1
kind: Config
ai:
  providers:
    cloud:
      protocol: openai
      baseURL: http://127.0.0.1:1/v1
      apiKeyEnv: OWTF_TEST_AI_UNSET
  models:
    z:
      provider: cloud
      model: model-z
    a:
      provider: cloud
      model: model-a
  defaultModel: a
`), 0600)
	if err != nil {
		t.Fatal(err)
	}
	t.Setenv("OWTF_TEST_AI_UNSET", "")
	var out, diagnostics bytes.Buffer
	if err := run([]string{"models", "list", "--config", path}, &out, &diagnostics); err != nil {
		t.Fatal(err)
	}
	if strings.Index(out.String(), `"alias": "a"`) > strings.Index(out.String(), `"alias": "z"`) || !strings.Contains(out.String(), `"default": true`) {
		t.Fatal(out.String())
	}
	out.Reset()
	if err := run([]string{"models", "check", "--config", path}, &out, &diagnostics); err == nil || !strings.Contains(err.Error(), "credential") {
		t.Fatalf("error=%v", err)
	}
	if out.Len() != 0 {
		t.Fatal("failure printed a success result")
	}
}

func TestModelsCommandValidation(t *testing.T) {
	for _, args := range [][]string{{"models"}, {"models", "other"}, {"models", "list", "extra"}, {"models", "list", "--model", "test"}} {
		var out bytes.Buffer
		if err := run(args, &out, &out); err == nil {
			t.Fatalf("accepted %v", args)
		}
	}
}
