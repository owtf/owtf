package ai

import (
	"bytes"
	"context"
	"io"
	"net/http"
	"sync/atomic"

	"charm.land/fantasy"
	"charm.land/fantasy/providers/anthropic"
	"charm.land/fantasy/providers/google"
	"charm.land/fantasy/providers/openai"
	"charm.land/fantasy/providers/openaicompat"
	"github.com/owtf/owtf/internal/config"
)

func newModel(ctx context.Context, p config.AIProvider, model, key string) (fantasy.LanguageModel, func(), error) {
	transport := http.DefaultTransport.(*http.Transport).Clone()
	// Model credentials and prompts must not enter OWTF's capture proxy just
	// because a shell used to run scanners has HTTP_PROXY configured.
	transport.Proxy = nil
	client := &http.Client{
		Transport:     &modelTransport{base: transport, protocol: p.Protocol, key: key},
		CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse },
	}
	base := p.BaseURL
	if base == "" {
		switch p.Protocol {
		case "openai":
			base = "https://api.openai.com/v1"
		case "anthropic":
			base = "https://api.anthropic.com"
		case "google":
			base = "https://generativelanguage.googleapis.com"
		}
	}
	var provider fantasy.Provider
	var err error
	switch p.Protocol {
	case "openai":
		provider, err = openai.New(openai.WithAPIKey(key), openai.WithBaseURL(base), openai.WithHTTPClient(client))
	case "anthropic":
		provider, err = anthropic.New(anthropic.WithAPIKey(key), anthropic.WithBaseURL(base), anthropic.WithHTTPClient(client))
	case "google":
		provider, err = google.New(google.WithGeminiAPIKey(key), google.WithBaseURL(base), google.WithHTTPClient(client))
	case "openaicompat":
		provider, err = openaicompat.New(openaicompat.WithAPIKey(key), openaicompat.WithBaseURL(base), openaicompat.WithHTTPClient(client))
	}
	if err != nil {
		transport.CloseIdleConnections()
		return nil, nil, err
	}
	languageModel, err := provider.LanguageModel(ctx, model)
	if err != nil {
		transport.CloseIdleConnections()
		return nil, nil, err
	}
	return languageModel, transport.CloseIdleConnections, nil
}

type requestBudgetKey struct{}

func oneRequest(ctx context.Context) context.Context {
	return context.WithValue(ctx, requestBudgetKey{}, new(atomic.Bool))
}

type modelTransport struct {
	base     http.RoundTripper
	protocol string
	key      string
}

// RoundTrip enforces one wire request per Generate even if a provider SDK adds
// retries in a future release. It also bounds decompressed response bytes.
func (t *modelTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	budget, ok := req.Context().Value(requestBudgetKey{}).(*atomic.Bool)
	if !ok || !budget.CompareAndSwap(false, true) {
		if req.Body != nil {
			_ = req.Body.Close()
		}
		return nil, &requestError{reason: "additional request blocked (no retries)"}
	}
	req = req.Clone(req.Context())
	// Prevent net/http itself from replaying a POST on a stale connection.
	req.GetBody = nil
	for _, h := range []string{"Authorization", "X-Api-Key", "X-Goog-Api-Key", "OpenAI-Organization", "OpenAI-Project"} {
		req.Header.Del(h)
	}
	if t.key != "" {
		switch t.protocol {
		case "anthropic":
			req.Header.Set("X-Api-Key", t.key)
		case "google":
			req.Header.Set("X-Goog-Api-Key", t.key)
		default:
			req.Header.Set("Authorization", "Bearer "+t.key)
		}
	}
	response, err := t.base.RoundTrip(req)
	if err != nil {
		return nil, &requestError{reason: "transport error (not retried)"}
	}
	defer response.Body.Close()
	if response.StatusCode < 200 || response.StatusCode >= 300 {
		return nil, &requestError{status: response.StatusCode}
	}
	const maximumResponse = 8 << 20
	body, err := io.ReadAll(io.LimitReader(response.Body, maximumResponse+1))
	if err != nil {
		return nil, &requestError{reason: "cannot read response"}
	}
	if len(body) > maximumResponse {
		return nil, &requestError{reason: "response exceeds 8 MiB limit"}
	}
	response.Body = io.NopCloser(bytes.NewReader(body))
	return response, nil
}
