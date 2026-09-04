package proxy

import (
	"context"
	"encoding/base64"
	"errors"
	"io"
	"net/http"
	"strings"
	"testing"
	"time"
)

func TestLiveInterceptionContinuesWithRequestEdits(t *testing.T) {
	live := newLiveForTest(t)
	if err := live.Configure(LiveConfig{Enabled: true, Requests: true, TimeoutMS: 1000}); err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodPost, "https://example.test/before", strings.NewReader("before"))
	request.Header.Set("X-Before", "true")
	done := make(chan error, 1)
	go func() { done <- live.interceptRequest(context.Background(), request) }()

	pending := waitForPending(t, live)
	method := http.MethodPut
	url := "https://example.test/after"
	headers := http.Header{"X-After": {"true"}}
	body := base64.StdEncoding.EncodeToString([]byte("after"))
	if _, err := live.Continue(pending.ID, InterceptionUpdate{
		Method: &method, URL: &url, Headers: &headers, BodyBase64: &body,
	}); err != nil {
		t.Fatal(err)
	}
	if err := <-done; err != nil {
		t.Fatal(err)
	}
	requestBody, _ := io.ReadAll(request.Body)
	if request.Method != http.MethodPut || request.URL.String() != url || request.Header.Get("X-After") != "true" || string(requestBody) != "after" {
		t.Fatalf("edited request = %s %s headers=%v body=%q", request.Method, request.URL, request.Header, requestBody)
	}
	if request.Header.Get("Content-Length") != "5" || request.ContentLength != 5 {
		t.Fatalf("edited request length = %d, header = %q", request.ContentLength, request.Header.Get("Content-Length"))
	}
}

func TestLiveInterceptionDropsResponse(t *testing.T) {
	live := newLiveForTest(t)
	if err := live.Configure(LiveConfig{Enabled: true, Responses: true, TimeoutMS: 1000}); err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodGet, "https://example.test/", nil)
	response := &http.Response{
		StatusCode: http.StatusOK, Header: make(http.Header),
		Body: io.NopCloser(strings.NewReader("response")), Request: request,
	}
	done := make(chan error, 1)
	go func() { done <- live.interceptResponse(context.Background(), response) }()
	pending := waitForPending(t, live)
	if pending.Phase != "response" || pending.StatusCode != http.StatusOK {
		t.Fatalf("pending response = %+v", pending)
	}
	if _, err := live.Drop(pending.ID); err != nil {
		t.Fatal(err)
	}
	if err := <-done; !errors.Is(err, ErrInterceptionDropped) {
		t.Fatalf("drop error = %v", err)
	}
}

func TestLiveInterceptionTimesOutAndCloseReleasesWaiters(t *testing.T) {
	live := newLiveForTest(t)
	if err := live.Configure(LiveConfig{Enabled: true, Requests: true, TimeoutMS: 100}); err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodGet, "https://example.test/timeout", nil)
	started := time.Now()
	if err := live.interceptRequest(context.Background(), request); err != nil {
		t.Fatal(err)
	}
	if elapsed := time.Since(started); elapsed < 75*time.Millisecond || elapsed > time.Second {
		t.Fatalf("timeout elapsed = %s", elapsed)
	}
	if pending := live.Pending(); len(pending) != 0 {
		t.Fatalf("timed-out pending = %+v", pending)
	}

	request, _ = http.NewRequest(http.MethodGet, "https://example.test/close", nil)
	done := make(chan error, 1)
	go func() { done <- live.interceptRequest(context.Background(), request) }()
	waitForPending(t, live)
	live.Close()
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("close result = %v", err)
		}
	case <-time.After(time.Second):
		t.Fatal("close did not release pending interception")
	}
}

func TestLiveInterceptionRejectsUnsafeEditsWithoutResolving(t *testing.T) {
	live := newLiveForTest(t)
	if err := live.Configure(LiveConfig{Enabled: true, Requests: true, TimeoutMS: 1000}); err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodGet, "https://example.test/", nil)
	done := make(chan error, 1)
	go func() { done <- live.interceptRequest(context.Background(), request) }()
	pending := waitForPending(t, live)
	headers := http.Header{"X-Test": {"safe\r\ninjected: true"}}
	if _, err := live.Continue(pending.ID, InterceptionUpdate{Headers: &headers}); err == nil {
		t.Fatal("header injection was accepted")
	}
	if _, err := live.Get(pending.ID); err != nil {
		t.Fatalf("invalid edit resolved pending request: %v", err)
	}
	if _, err := live.Continue(pending.ID, InterceptionUpdate{}); err != nil {
		t.Fatal(err)
	}
	if err := <-done; err != nil {
		t.Fatal(err)
	}
}

func newLiveForTest(t *testing.T) *LiveInterception {
	t.Helper()
	live, err := NewLiveInterception(1024, 10)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(live.Close)
	return live
}

func waitForPending(t *testing.T, live *LiveInterception) PendingInterception {
	t.Helper()
	deadline := time.Now().Add(time.Second)
	for time.Now().Before(deadline) {
		if pending := live.Pending(); len(pending) > 0 {
			return pending[0]
		}
		time.Sleep(time.Millisecond)
	}
	t.Fatal("interception did not become pending")
	return PendingInterception{}
}
