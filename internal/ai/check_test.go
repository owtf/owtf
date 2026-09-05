package ai

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"regexp"
	"strconv"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/owtf/owtf/internal/config"
)

var protocols = []string{"openai", "openaicompat", "anthropic", "google"}
var noncePattern = regexp.MustCompile(`[a-f0-9]{32}`)

func testSettings(protocol, endpoint string) config.AI {
	return config.AI{
		Providers:    map[string]config.AIProvider{"test": {Protocol: protocol, BaseURL: endpoint, APIKeyEnv: "OWTF_TEST_AI_KEY"}},
		Models:       map[string]config.AIModel{"probe": {Provider: "test", Model: "probe-model"}},
		DefaultModel: "probe", TimeoutSeconds: 2,
	}
}

// wireResponse is a provider fixture, not a real model. Tests exercise Fantasy's
// actual request/response conversion against each documented HTTP protocol.
func wireResponse(protocol, nonce, name string, tool bool) any {
	args := map[string]string{"nonce": nonce}
	encoded, _ := json.Marshal(args)
	switch protocol {
	case "anthropic":
		content := []any{map[string]any{"type": "text", "text": string(encoded)}}
		reason := "end_turn"
		if tool {
			content = []any{map[string]any{"type": "tool_use", "id": "call_probe", "name": name, "input": args}}
			reason = "tool_use"
		}
		return map[string]any{"id": "msg_probe", "type": "message", "role": "assistant", "model": "probe-model", "content": content, "stop_reason": reason, "usage": map[string]int{"input_tokens": 10, "output_tokens": 10}}
	case "google":
		part := map[string]any{"text": string(encoded)}
		if tool {
			part = map[string]any{"functionCall": map[string]any{"name": name, "args": args}}
		}
		return map[string]any{"candidates": []any{map[string]any{"content": map[string]any{"role": "model", "parts": []any{part}}, "finishReason": "STOP"}}, "usageMetadata": map[string]int{"promptTokenCount": 10, "candidatesTokenCount": 10, "totalTokenCount": 20}}
	default:
		message := map[string]any{"role": "assistant", "content": string(encoded)}
		reason := "stop"
		if tool {
			message = map[string]any{"role": "assistant", "tool_calls": []any{map[string]any{"id": "call_probe", "type": "function", "function": map[string]any{"name": name, "arguments": string(encoded)}}}}
			reason = "tool_calls"
		}
		return map[string]any{"id": "chatcmpl-probe", "object": "chat.completion", "model": "probe-model", "choices": []any{map[string]any{"index": 0, "message": message, "finish_reason": reason}}}
	}
}

func TestCheckProviderRoundTrips(t *testing.T) {
	t.Setenv("OWTF_TEST_AI_KEY", "explicit-key")
	t.Setenv("OPENAI_API_KEY", "ambient-key-must-not-leak")
	t.Setenv("ANTHROPIC_AUTH_TOKEN", "ambient-token-must-not-leak")
	for _, protocol := range protocols {
		t.Run(protocol, func(t *testing.T) {
			var count atomic.Int32
			var first string
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				n := count.Add(1)
				body, _ := io.ReadAll(r.Body)
				if r.Method != "POST" {
					t.Errorf("method = %s", r.Method)
				}
				for _, values := range r.Header {
					for _, value := range values {
						if strings.Contains(value, "ambient-") {
							t.Error("ambient credential leaked")
						}
					}
				}
				header := "Authorization"
				expected := "Bearer explicit-key"
				if protocol == "anthropic" {
					header = "X-Api-Key"
					expected = "explicit-key"
				}
				if protocol == "google" {
					header = "X-Goog-Api-Key"
					expected = "explicit-key"
				}
				if r.Header.Get(header) != expected {
					t.Errorf("missing explicit credential header %s", header)
				}
				if r.URL.Query().Get("key") != "" {
					t.Error("API key in query")
				}
				values := noncePattern.FindAllString(string(body), -1)
				if len(values) == 0 {
					t.Error("missing nonce")
					http.Error(w, "bad fixture request", 400)
					return
				}
				nonce := values[len(values)-1]
				if n == 1 {
					first = nonce
				} else if nonce == first {
					t.Error("tool result must carry a fresh nonce")
				}
				if !strings.Contains(string(body), "echo_probe") || !strings.Contains(string(body), "probe-model") && protocol != "google" {
					t.Error("missing configured model or tool")
				}
				w.Header().Set("Content-Type", "application/json")
				_ = json.NewEncoder(w).Encode(wireResponse(protocol, nonce, "echo_probe", n == 1))
			}))
			defer server.Close()
			result, err := Check(context.Background(), testSettings(protocol, server.URL), "")
			if err != nil {
				t.Fatal(err)
			}
			if count.Load() != 2 || !result.ToolRoundTrip || !result.ValidatedJSON || result.Model != "probe-model" {
				t.Fatalf("result=%+v requests=%d", result, count.Load())
			}
		})
	}
}

func TestCheckHTTPFailuresDoNotRetryOrLeak(t *testing.T) {
	t.Setenv("OWTF_TEST_AI_KEY", "private-test-key")
	for _, protocol := range protocols {
		for _, status := range []int{401, 429, 500, 503} {
			t.Run(protocol+"/"+http.StatusText(status), func(t *testing.T) {
				var count atomic.Int32
				server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
					count.Add(1)
					w.WriteHeader(status)
					_, _ = io.WriteString(w, "private-test-key sensitive-provider-body")
				}))
				defer server.Close()
				_, err := Check(context.Background(), testSettings(protocol, server.URL), "probe")
				if err == nil || count.Load() != 1 {
					t.Fatalf("error=%v requests=%d", err, count.Load())
				}
				if !strings.Contains(err.Error(), "HTTP "+strconv.Itoa(status)) {
					t.Fatalf("lost sanitized status: %v", err)
				}
				if strings.Contains(err.Error(), "private-test-key") || strings.Contains(err.Error(), "sensitive-provider-body") {
					t.Fatal("provider error leaked")
				}
			})
		}
	}
}

func TestCheckInvalidToolStopsBeforeSecondRequest(t *testing.T) {
	t.Setenv("OWTF_TEST_AI_KEY", "test")
	for _, name := range []string{"run_plugin", "echo_probe"} {
		t.Run(name, func(t *testing.T) {
			var count atomic.Int32
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				count.Add(1)
				w.Header().Set("Content-Type", "application/json")
				_ = json.NewEncoder(w).Encode(wireResponse("openai", "wrong-nonce", name, true))
			}))
			defer server.Close()
			_, err := Check(context.Background(), testSettings("openai", server.URL), "")
			if err == nil || count.Load() != 1 {
				t.Fatalf("error=%v requests=%d", err, count.Load())
			}
		})
	}
}

func TestCheckCancellation(t *testing.T) {
	t.Setenv("OWTF_TEST_AI_KEY", "test")
	for _, protocol := range protocols {
		t.Run(protocol, func(t *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			var count atomic.Int32
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				count.Add(1)
				_, _ = io.Copy(io.Discard, r.Body)
				cancel()
				<-r.Context().Done()
			}))
			defer server.Close()
			started := time.Now()
			_, err := Check(ctx, testSettings(protocol, server.URL), "")
			if !errors.Is(err, context.Canceled) || count.Load() != 1 || time.Since(started) > time.Second {
				t.Fatalf("cancellation error=%v requests=%d", err, count.Load())
			}
		})
	}
}

func TestStrictNonce(t *testing.T) {
	for _, value := range []string{`{"nonce":"ok"}`, " \n{\"nonce\":\"ok\"}\n"} {
		if !validNonce(value, "ok") {
			t.Fatalf("rejected %s", value)
		}
	}
	for _, value := range []string{`{"nonce":"wrong"}`, `{"nonce":"ok","other":true}`, `{"nonce":"ok","nonce":"ok"}`, `{"Nonce":"ok"}`, `{"nonce":null}`, `{"nonce":1}`, `{"nonce":"ok"} {}`, "```json\n{\"nonce\":\"ok\"}\n```", `[]`, `null`} {
		if validNonce(value, "ok") {
			t.Fatalf("accepted %s", value)
		}
	}
}

func TestCheckMissingCredentialsDoesNotSend(t *testing.T) {
	t.Setenv("OWTF_TEST_AI_KEY", "")
	var count atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { count.Add(1) }))
	defer server.Close()
	if _, err := Check(context.Background(), testSettings("openai", server.URL), ""); err == nil || count.Load() != 0 {
		t.Fatalf("error=%v requests=%d", err, count.Load())
	}
}

func TestCheckRejectsIncompleteRoundTrips(t *testing.T) {
	t.Setenv("OWTF_TEST_AI_KEY", "test")
	for _, mode := range []string{"text-only", "multiple-tools", "wrong-result", "truncated"} {
		t.Run(mode, func(t *testing.T) {
			var count atomic.Int32
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				n := count.Add(1)
				body, _ := io.ReadAll(r.Body)
				nonces := noncePattern.FindAllString(string(body), -1)
				nonce := nonces[len(nonces)-1]
				if mode == "wrong-result" && n == 2 {
					nonce = "wrong"
				}
				response := wireResponse("openai", nonce, "echo_probe", n == 1 && mode != "text-only").(map[string]any)
				choice := response["choices"].([]any)[0].(map[string]any)
				if mode == "multiple-tools" {
					message := choice["message"].(map[string]any)
					calls := message["tool_calls"].([]any)
					message["tool_calls"] = append(calls, calls[0])
				}
				if mode == "truncated" {
					choice["finish_reason"] = "length"
				}
				w.Header().Set("Content-Type", "application/json")
				_ = json.NewEncoder(w).Encode(response)
			}))
			defer server.Close()
			result, err := Check(context.Background(), testSettings("openai", server.URL), "")
			want := int32(1)
			if mode == "wrong-result" {
				want = 2
			}
			if err == nil || result.ToolRoundTrip || count.Load() != want {
				t.Fatalf("result=%+v err=%v requests=%d", result, err, count.Load())
			}
		})
	}
}
