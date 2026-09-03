package proxy

import (
	"io"
	"net/http"
	"strings"
	"testing"
)

func TestResponseCacheFiltersCookieIdentity(t *testing.T) {
	cache, err := NewResponseCache(CacheOptions{
		MaximumEntries: 2, MaximumBody: 1024, CookieBlacklist: []string{"_ga"},
	})
	if err != nil {
		t.Fatal(err)
	}
	requests := 0
	transport := cache.RoundTripper(roundTripperFunc(func(request *http.Request) (*http.Response, error) {
		requests++
		response := testResponse(request, http.StatusOK, "response")
		response.Header.Add("X-Test", "one")
		response.Header.Add("X-Test", "two")
		return response, nil
	}))

	for _, cookie := range []string{"session=one; _ga=first", "_ga=second; session=one"} {
		request, _ := http.NewRequest(http.MethodGet, "https://example.test/path", nil)
		request.Header.Set("Cookie", cookie)
		response, err := transport.RoundTrip(request)
		if err != nil {
			t.Fatal(err)
		}
		body, _ := io.ReadAll(response.Body)
		response.Body.Close()
		if string(body) != "response" || len(response.Header.Values("X-Test")) != 2 {
			t.Fatalf("cached response changed: headers=%v body=%q", response.Header, body)
		}
	}
	if requests != 1 {
		t.Fatalf("upstream requests = %d, want 1", requests)
	}

	request, _ := http.NewRequest(http.MethodGet, "https://example.test/path", nil)
	request.Header.Set("Cookie", "session=two")
	response, err := transport.RoundTrip(request)
	if err != nil {
		t.Fatal(err)
	}
	response.Body.Close()
	if requests != 2 {
		t.Fatalf("distinct session cookie reused cache; requests = %d", requests)
	}
}

func TestResponseCacheDoesNotTruncateLargeResponses(t *testing.T) {
	cache, err := NewResponseCache(CacheOptions{MaximumEntries: 1, MaximumBody: 4})
	if err != nil {
		t.Fatal(err)
	}
	requests := 0
	transport := cache.RoundTripper(roundTripperFunc(func(request *http.Request) (*http.Response, error) {
		requests++
		return testResponse(request, http.StatusOK, "larger than cache"), nil
	}))
	for range 2 {
		request, _ := http.NewRequest(http.MethodGet, "https://example.test/large", nil)
		response, err := transport.RoundTrip(request)
		if err != nil {
			t.Fatal(err)
		}
		body, _ := io.ReadAll(response.Body)
		response.Body.Close()
		if string(body) != "larger than cache" {
			t.Fatalf("body was truncated: %q", body)
		}
	}
	if requests != 2 {
		t.Fatalf("large response was cached; requests = %d", requests)
	}
}

func TestResponseCacheHonorsNoStore(t *testing.T) {
	cache, _ := NewResponseCache(CacheOptions{MaximumEntries: 1, MaximumBody: 1024})
	requests := 0
	transport := cache.RoundTripper(roundTripperFunc(func(request *http.Request) (*http.Response, error) {
		requests++
		response := testResponse(request, http.StatusOK, strings.Repeat("x", 4))
		response.Header.Set("Cache-Control", "public, no-store")
		return response, nil
	}))
	for range 2 {
		request, _ := http.NewRequest(http.MethodGet, "https://example.test/no-store", nil)
		response, _ := transport.RoundTrip(request)
		response.Body.Close()
	}
	if requests != 2 {
		t.Fatalf("no-store response was cached; requests = %d", requests)
	}
}
