package config

import (
	"errors"
	"fmt"
	"net"
	"net/url"
	"regexp"
	"strings"
)

// AI names provider connections and model aliases. Merely configuring a model
// never enables network calls. Credentials are environment references only.
type AI struct {
	Providers       map[string]AIProvider `json:"providers" yaml:"providers"`
	Models          map[string]AIModel    `json:"models" yaml:"models"`
	DefaultModel    string                `json:"default_model,omitempty" yaml:"defaultModel"`
	TimeoutSeconds  int                   `json:"timeout_seconds,omitempty" yaml:"timeoutSeconds"`
	MaxOutputTokens int64                 `json:"max_output_tokens,omitempty" yaml:"maxOutputTokens"`
}

// AIProvider selects a wire protocol, not a fixed list of vendor model IDs.
type AIProvider struct {
	Protocol  string `json:"protocol" yaml:"protocol"`
	BaseURL   string `json:"base_url,omitempty" yaml:"baseURL"`
	APIKeyEnv string `json:"api_key_env,omitempty" yaml:"apiKeyEnv"`
}

// AIModel gives an operator-selected model ID a stable local alias.
type AIModel struct {
	Provider string `json:"provider" yaml:"provider"`
	Model    string `json:"model" yaml:"model"`
}

var aiName = regexp.MustCompile(`^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$`)
var envName = regexp.MustCompile(`^[a-zA-Z_][a-zA-Z0-9_]*$`)

// Validate rejects ambiguous provider selection and credentials in URLs.
func (a AI) Validate() error {
	if a.TimeoutSeconds < 0 || a.TimeoutSeconds > 120 {
		return errors.New("ai.timeoutSeconds must be between 1 and 120, or 0 for the 30-second default")
	}
	if a.MaxOutputTokens < 0 || a.MaxOutputTokens > 4096 {
		return errors.New("ai.maxOutputTokens must be between 1 and 4096, or 0 for the 1024-token default")
	}
	for name, p := range a.Providers {
		if !aiName.MatchString(name) {
			return errors.New("invalid AI provider name")
		}
		switch p.Protocol {
		case "openai", "anthropic", "google", "openaicompat":
		default:
			return fmt.Errorf("AI provider %s: unsupported protocol", name)
		}
		if p.APIKeyEnv != "" && !envName.MatchString(p.APIKeyEnv) {
			return fmt.Errorf("AI provider %s: invalid apiKeyEnv reference", name)
		}
		if p.APIKeyEnv == "" && p.Protocol != "openaicompat" {
			return fmt.Errorf("AI provider %s: apiKeyEnv is required", name)
		}
		if p.BaseURL == "" && p.Protocol == "openaicompat" {
			return fmt.Errorf("AI provider %s: baseURL is required", name)
		}
		if p.BaseURL != "" {
			u, err := url.Parse(p.BaseURL)
			if err != nil || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.ForceQuery || u.Fragment != "" || u.Opaque != "" {
				return fmt.Errorf("AI provider %s: baseURL must be an absolute URL without credentials, query, or fragment", name)
			}
			local := u.Hostname() == "localhost" || net.ParseIP(u.Hostname()).IsLoopback()
			if u.Scheme != "https" && !(u.Scheme == "http" && local) {
				return fmt.Errorf("AI provider %s: baseURL requires HTTPS except on loopback", name)
			}
		}
	}
	for name, m := range a.Models {
		if !aiName.MatchString(name) {
			return errors.New("invalid AI model alias")
		}
		p, ok := a.Providers[m.Provider]
		if !ok {
			return fmt.Errorf("AI model %s: provider is not configured", name)
		}
		if strings.TrimSpace(m.Model) != m.Model || m.Model == "" || len(m.Model) > 256 || strings.ContainsAny(m.Model, "\r\n\x00") {
			return fmt.Errorf("AI model %s: invalid model ID", name)
		}
		// Fantasy routes these names to Vertex Anthropic automatically. This
		// qualification path intentionally supports explicit Gemini API access only.
		if p.Protocol == "google" && (strings.Contains(m.Model, "claude") || strings.Contains(m.Model, "anthropic")) {
			return fmt.Errorf("AI model %s: use the anthropic protocol for Anthropic models", name)
		}
	}
	if a.DefaultModel != "" {
		if _, ok := a.Models[a.DefaultModel]; !ok {
			return errors.New("ai.defaultModel must name a configured model alias")
		}
	}
	return nil
}
