package ai

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
)

func TestMissingGoogleUsageDoesNotCrash(t *testing.T) {
	t.Setenv("OWTF_TEST_AI_KEY", "test")
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		response := wireResponse("google", noncePattern.FindString(string(body)), "echo_probe", true).(map[string]any)
		delete(response, "usageMetadata")
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()
	if _, err := Check(context.Background(), testSettings("google", server.URL), ""); err == nil {
		t.Fatal("malformed SDK response passed qualification")
	}
}

func TestTransportBudget(t *testing.T) {
	var requests atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { requests.Add(1); _, _ = io.WriteString(w, "{}") }))
	defer server.Close()
	transport := &modelTransport{base: http.DefaultTransport}
	ctx := oneRequest(context.Background())
	for n := 0; n < 2; n++ {
		req, _ := http.NewRequestWithContext(ctx, http.MethodPost, server.URL, nil)
		resp, err := transport.RoundTrip(req)
		if n == 0 {
			if err != nil {
				t.Fatal(err)
			}
			resp.Body.Close()
		} else if err == nil {
			resp.Body.Close()
			t.Fatal("allowed second wire request")
		}
	}
	if requests.Load() != 1 {
		t.Fatalf("requests=%d", requests.Load())
	}
}

func TestCheckRedirectBlocked(t *testing.T) {
	t.Setenv("OWTF_TEST_AI_KEY", "secret")
	var leaked atomic.Int32
	other := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { leaked.Add(1) }))
	defer other.Close()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { http.Redirect(w, r, other.URL, 307) }))
	defer server.Close()
	for _, protocol := range protocols {
		t.Run(protocol, func(t *testing.T) {
			if _, err := Check(context.Background(), testSettings(protocol, server.URL), ""); err == nil {
				t.Fatal("accepted redirect")
			}
		})
	}
	if leaked.Load() != 0 {
		t.Fatal("followed credential-bearing redirect")
	}
}

func TestCheckLargeAndMalformedResponses(t *testing.T) {
	t.Setenv("OWTF_TEST_AI_KEY", "secret")
	for _, body := range []string{strings.Repeat("x", (8<<20)+1), `{"sensitive":"secret" garbage`} {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			_, _ = io.WriteString(w, body)
		}))
		_, err := Check(context.Background(), testSettings("openai", server.URL), "")
		server.Close()
		if err == nil || strings.Contains(err.Error(), "secret") {
			t.Fatalf("error=%v", err)
		}
	}
}

func TestUnauthenticatedLocalModelDoesNotInheritKey(t *testing.T) {
	t.Setenv("OPENAI_API_KEY", "ambient-secret")
	var requests atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requests.Add(1)
		if r.Header.Get("Authorization") != "" {
			t.Error("ambient credential leaked to local endpoint")
		}
		w.WriteHeader(400)
	}))
	defer server.Close()
	a := testSettings("openaicompat", server.URL)
	p := a.Providers["test"]
	p.APIKeyEnv = ""
	a.Providers["test"] = p
	_, err := Check(context.Background(), a, "")
	if err == nil || requests.Load() != 1 {
		t.Fatalf("error=%v requests=%d", err, requests.Load())
	}
}
