package config

import (
	"strings"
	"testing"
)

func TestAIConfiguration(t *testing.T) {
	valid := func() AI {
		return AI{
			Providers: map[string]AIProvider{"local": {Protocol: "openaicompat", BaseURL: "http://127.0.0.1:11434/v1"}},
			Models:    map[string]AIModel{"review": {Provider: "local", Model: "arbitrary/model:version"}}, DefaultModel: "review",
		}
	}
	if err := valid().Validate(); err != nil {
		t.Fatal(err)
	}
	if err := (AI{}).Validate(); err != nil {
		t.Fatal(err)
	}
	tests := map[string]func(*AI){
		"unsupported protocol":  func(a *AI) { a.Providers["local"] = AIProvider{Protocol: "other"} },
		"missing URL":           func(a *AI) { a.Providers["local"] = AIProvider{Protocol: "openaicompat"} },
		"missing key reference": func(a *AI) { a.Providers["local"] = AIProvider{Protocol: "openai"} },
		"invalid key reference": func(a *AI) { p := a.Providers["local"]; p.APIKeyEnv = "secret value"; a.Providers["local"] = p },
		"unknown provider":      func(a *AI) { a.Models["review"] = AIModel{Provider: "missing", Model: "test"} },
		"unknown default":       func(a *AI) { a.DefaultModel = "missing" },
		"empty model":           func(a *AI) { a.Models["review"] = AIModel{Provider: "local"} },
		"invalid alias":         func(a *AI) { a.Models["bad\nname"] = a.Models["review"] },
		"negative timeout":      func(a *AI) { a.TimeoutSeconds = -1 },
		"unbounded timeout":     func(a *AI) { a.TimeoutSeconds = 121 },
		"negative tokens":       func(a *AI) { a.MaxOutputTokens = -1 },
		"unbounded tokens":      func(a *AI) { a.MaxOutputTokens = 4097 },
		"implicit Google provider switch": func(a *AI) {
			a.Providers["local"] = AIProvider{Protocol: "google", APIKeyEnv: "TEST_KEY"}
			a.Models["review"] = AIModel{Provider: "local", Model: "claude-test"}
		},
	}
	for name, mutate := range tests {
		t.Run(name, func(t *testing.T) {
			a := valid()
			mutate(&a)
			if a.Validate() == nil {
				t.Fatal("expected validation failure")
			}
		})
	}
	for _, endpoint := range []string{"http://remote.test/v1", "https://user:secret@remote.test", "https://remote.test?key=secret", "https://remote.test#secret", "https://remote.test?", "/v1", "file:///tmp/model"} {
		t.Run(endpoint, func(t *testing.T) {
			a := valid()
			a.Providers["local"] = AIProvider{Protocol: "openaicompat", BaseURL: endpoint}
			err := a.Validate()
			if err == nil || strings.Contains(err.Error(), "secret") {
				t.Fatalf("unsafe validation result: %v", err)
			}
		})
	}
}

func TestAIYAMLSecretsAreReferencesOnly(t *testing.T) {
	for _, field := range []string{"apiKey", "password", "token"} {
		_, err := Load(writeConfig(t, "apiVersion: owtf.dev/v1alpha1\nkind: Config\nai:\n  providers:\n    test:\n      protocol: openai\n      "+field+": secret\n"))
		if err == nil {
			t.Fatalf("accepted literal credential %s", field)
		}
	}
	loaded, err := Load(writeConfig(t, `apiVersion: owtf.dev/v1alpha1
kind: Config
ai:
  providers:
    cloud:
      protocol: anthropic
      apiKeyEnv: OWTF_TEST_KEY
  models:
    review:
      provider: cloud
      model: operator-selected-model
  defaultModel: review
`))
	if err != nil {
		t.Fatal(err)
	}
	if loaded.AI.DefaultModel != "review" || loaded.AI.Providers["cloud"].APIKeyEnv != "OWTF_TEST_KEY" {
		t.Fatalf("unexpected AI config: %+v", loaded.AI)
	}
}
