package proxy

import (
	"bytes"
	"context"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"
	"time"

	"github.com/owtf/owtf/internal/har"
)

type doerFunc func(*http.Request) (*http.Response, error)

func (function doerFunc) Do(request *http.Request) (*http.Response, error) {
	return function(request)
}

func TestAPIServesCAHistoryStatsAndClear(t *testing.T) {
	recorder := NewRecorder(10)
	for _, transaction := range []har.Transaction{
		{
			Method: "GET", URL: "https://example.test/one", RequestHeaders: `{}`,
			StatusCode: 200, ResponseHeaders: `{}`, ResponseBody: []byte("public"), StartedAt: time.Now(),
		},
		{
			Method: "POST", URL: "https://example.test/two", RequestHeaders: `{"X-Test":["one"]}`,
			RequestBody: []byte("needle"), StatusCode: 404, ResponseHeaders: `{}`, StartedAt: time.Now(),
		},
	} {
		if err := recorder.Record(transaction); err != nil {
			t.Fatal(err)
		}
	}
	authority, _, handler := newAPIForTest(t, recorder, doerFunc(func(*http.Request) (*http.Response, error) {
		return nil, context.Canceled
	}), 1024)
	server := httptest.NewServer(handler)
	defer server.Close()

	response, err := http.Get(server.URL + "/api/v2/transactions?method=post&search=NEEDLE&limit=1")
	if err != nil {
		t.Fatal(err)
	}
	var history []transactionSummary
	decodeTestResponse(t, response, http.StatusOK, &history)
	if len(history) != 1 || history[0].ID != 2 || history[0].RequestBytes != len("needle") {
		t.Fatalf("history = %+v", history)
	}

	response, err = http.Get(server.URL + "/api/v2/transactions/2")
	if err != nil {
		t.Fatal(err)
	}
	var single historyTransaction
	decodeTestResponse(t, response, http.StatusOK, &single)
	if single.URL != "https://example.test/two" || single.RequestHeaders.Get("X-Test") != "one" ||
		single.RequestBodyBase64 != base64.StdEncoding.EncodeToString([]byte("needle")) {
		t.Fatalf("transaction = %+v", single)
	}

	response, err = http.Get(server.URL + "/api/v2/transactions/stats")
	if err != nil {
		t.Fatal(err)
	}
	var stats transactionStats
	decodeTestResponse(t, response, http.StatusOK, &stats)
	if stats.Total != 2 || stats.Methods["POST"] != 1 || stats.Statuses[404] != 1 {
		t.Fatalf("stats = %+v", stats)
	}

	response, err = http.Get(server.URL + "/api/v2/ca")
	if err != nil {
		t.Fatal(err)
	}
	certificate, _ := io.ReadAll(response.Body)
	response.Body.Close()
	if response.StatusCode != http.StatusOK || !bytes.Equal(certificate, authority.CertificatePEM()) {
		t.Fatalf("CA response status = %d", response.StatusCode)
	}
	block := x509.NewCertPool()
	if !block.AppendCertsFromPEM(certificate) {
		t.Fatal("proxy API returned an invalid CA certificate")
	}

	request, _ := http.NewRequest(http.MethodDelete, server.URL+"/api/v2/transactions", nil)
	response, err = http.DefaultClient.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	var cleared map[string]int
	decodeTestResponse(t, response, http.StatusOK, &cleared)
	if cleared["removed"] != 2 || recorder.Stats().Total != 0 {
		t.Fatalf("clear = %v, stats = %+v", cleared, recorder.Stats())
	}
}

func TestAPIRepeaterUsesBoundedBinaryBodies(t *testing.T) {
	repeatClient := doerFunc(func(request *http.Request) (*http.Response, error) {
		body, _ := io.ReadAll(request.Body)
		if request.Method != http.MethodPatch || request.URL.String() != "https://example.test/item" ||
			request.Header.Get("X-Test") != "one" || string(body) != "data" {
			t.Fatalf("repeated request = %s %s headers=%v body=%q", request.Method, request.URL, request.Header, body)
		}
		return &http.Response{
			StatusCode: http.StatusCreated, Header: http.Header{"X-Upstream": {"yes"}},
			Body: io.NopCloser(bytes.NewReader([]byte("12345"))),
		}, nil
	})
	_, _, handler := newAPIForTest(t, NewRecorder(10), repeatClient, 4)
	server := httptest.NewServer(handler)
	defer server.Close()
	input := RepeatRequest{
		Method: "patch", URL: "https://example.test/item",
		Headers: http.Header{"X-Test": {"one"}}, BodyBase64: base64.StdEncoding.EncodeToString([]byte("data")),
	}
	data, _ := json.Marshal(input)
	response, err := http.Post(server.URL+"/api/v2/repeater", "application/json", bytes.NewReader(data))
	if err != nil {
		t.Fatal(err)
	}
	var result RepeatResponse
	decodeTestResponse(t, response, http.StatusOK, &result)
	if result.StatusCode != http.StatusCreated || !result.Truncated ||
		result.BodyBase64 != base64.StdEncoding.EncodeToString([]byte("1234")) || result.Headers.Get("X-Upstream") != "yes" {
		t.Fatalf("repeat response = %+v", result)
	}
}

func TestAPIRejectsInvalidFiltersAndRepeaterRequests(t *testing.T) {
	_, _, handler := newAPIForTest(t, NewRecorder(10), doerFunc(func(*http.Request) (*http.Response, error) {
		t.Fatal("invalid repeater request reached client")
		return nil, nil
	}), 4)
	server := httptest.NewServer(handler)
	defer server.Close()

	response, err := http.Get(server.URL + "/api/v2/transactions?unknown=true")
	if err != nil {
		t.Fatal(err)
	}
	decodeTestResponse(t, response, http.StatusBadRequest, &map[string]string{})

	for name, input := range map[string]RepeatRequest{
		"connect":        {Method: http.MethodConnect, URL: "https://example.test"},
		"relative URL":   {Method: http.MethodGet, URL: "/relative"},
		"invalid base64": {Method: http.MethodPost, URL: "https://example.test", BodyBase64: "!"},
		"large body":     {Method: http.MethodPost, URL: "https://example.test", BodyBase64: base64.StdEncoding.EncodeToString([]byte("12345"))},
		"unsafe header":  {Method: http.MethodGet, URL: "https://example.test", Headers: http.Header{"Connection": {"close"}}},
	} {
		t.Run(name, func(t *testing.T) {
			data, _ := json.Marshal(input)
			response, err := http.Post(server.URL+"/api/v2/repeater", "application/json", bytes.NewReader(data))
			if err != nil {
				t.Fatal(err)
			}
			decodeTestResponse(t, response, http.StatusBadRequest, &map[string]string{})
		})
	}
}

func TestAPIManagesInterceptorsAtomically(t *testing.T) {
	_, interceptors, handler := newAPIForTest(t, NewRecorder(10), doerFunc(func(*http.Request) (*http.Response, error) {
		return nil, context.Canceled
	}), 1024)
	if err := interceptors.Replace([]InterceptorRule{{Name: "initial", Phase: "request"}}); err != nil {
		t.Fatal(err)
	}
	server := httptest.NewServer(handler)
	defer server.Close()

	response, err := http.Get(server.URL + "/api/v2/interceptors")
	if err != nil {
		t.Fatal(err)
	}
	var config InterceptorConfig
	decodeTestResponse(t, response, http.StatusOK, &config)
	if len(config.Rules) != 1 || config.Rules[0].Name != "initial" {
		t.Fatalf("initial interceptor config = %+v", config)
	}

	replacement := InterceptorConfig{Rules: []InterceptorRule{{
		Name: "runtime", Phase: "request",
		Action: InterceptorAction{SetHeaders: map[string]string{"X-OWTF": "runtime"}},
	}}}
	response = proxyJSONRequest(t, http.MethodPut, server.URL+"/api/v2/interceptors", replacement)
	decodeTestResponse(t, response, http.StatusOK, &config)
	if len(config.Rules) != 1 || config.Rules[0].Name != "runtime" {
		t.Fatalf("replacement interceptor config = %+v", config)
	}

	response = proxyJSONRequest(t, http.MethodPatch, server.URL+"/api/v2/interceptors", map[string]any{
		"name": "runtime", "enabled": false,
	})
	var disabled InterceptorRule
	decodeTestResponse(t, response, http.StatusOK, &disabled)
	if disabled.Enabled == nil || *disabled.Enabled {
		t.Fatalf("disabled interceptor = %+v", disabled)
	}

	response = proxyJSONRequest(t, http.MethodPut, server.URL+"/api/v2/interceptors", InterceptorConfig{Rules: []InterceptorRule{{
		Name: "broken", Phase: "request", Match: InterceptorMatch{URLPattern: "["},
	}}})
	decodeTestResponse(t, response, http.StatusBadRequest, &map[string]string{})
	response = proxyJSONRequest(t, http.MethodPut, server.URL+"/api/v2/interceptors", json.RawMessage("null"))
	decodeTestResponse(t, response, http.StatusBadRequest, &map[string]string{})
	if active := interceptors.Config(); len(active.Rules) != 1 || active.Rules[0].Name != "runtime" || active.Rules[0].Enabled == nil || *active.Rules[0].Enabled {
		t.Fatalf("failed replacement changed active config: %+v", active)
	}

	response = proxyJSONRequest(t, http.MethodPatch, server.URL+"/api/v2/interceptors", map[string]any{
		"name": "missing", "enabled": true,
	})
	decodeTestResponse(t, response, http.StatusNotFound, &map[string]string{})
}

func TestAPIControlsLiveInterception(t *testing.T) {
	_, _, live, handler := newAPIForTestWithLive(t, NewRecorder(10), doerFunc(func(*http.Request) (*http.Response, error) {
		return nil, context.Canceled
	}), 1024)
	server := httptest.NewServer(handler)
	defer server.Close()
	response := proxyJSONRequest(t, http.MethodPut, server.URL+"/api/v2/interception", LiveConfig{
		Enabled: true, Requests: true, TimeoutMS: 1000,
	})
	var config LiveConfig
	decodeTestResponse(t, response, http.StatusOK, &config)
	if !config.Enabled || !config.Requests || config.Responses {
		t.Fatalf("live config = %+v", config)
	}

	request, _ := http.NewRequest(http.MethodGet, "https://example.test/api", nil)
	done := make(chan error, 1)
	go func() { done <- live.interceptRequest(context.Background(), request) }()
	waitForPending(t, live)
	response, err := http.Get(server.URL + "/api/v2/interception/pending")
	if err != nil {
		t.Fatal(err)
	}
	var pending []PendingInterception
	decodeTestResponse(t, response, http.StatusOK, &pending)
	if len(pending) != 1 || pending[0].URL != request.URL.String() {
		t.Fatalf("pending interceptions = %+v", pending)
	}
	updatedURL := "https://example.test/edited"
	response = proxyJSONRequest(t, http.MethodPost,
		server.URL+"/api/v2/interception/pending/"+pending[0].ID+"/continue",
		InterceptionUpdate{URL: &updatedURL})
	var resolved PendingInterception
	decodeTestResponse(t, response, http.StatusOK, &resolved)
	if err := <-done; err != nil || request.URL.String() != updatedURL {
		t.Fatalf("continued request URL = %s, error = %v", request.URL, err)
	}
	response, err = http.Get(server.URL + "/api/v2/interception/pending/" + pending[0].ID)
	if err != nil {
		t.Fatal(err)
	}
	decodeTestResponse(t, response, http.StatusNotFound, &map[string]string{})
}

func newAPIForTest(t *testing.T, recorder *Recorder, client httpDoer, maximumBody int64) (*Authority, *Interceptors, http.Handler) {
	t.Helper()
	authority, interceptors, _, handler := newAPIForTestWithLive(t, recorder, client, maximumBody)
	return authority, interceptors, handler
}

func newAPIForTestWithLive(t *testing.T, recorder *Recorder, client httpDoer, maximumBody int64) (*Authority, *Interceptors, *LiveInterception, http.Handler) {
	t.Helper()
	directory := t.TempDir()
	authority, err := LoadOrCreateAuthority(filepath.Join(directory, "ca.crt"), filepath.Join(directory, "ca.key"))
	if err != nil {
		t.Fatal(err)
	}
	interceptors, err := NewInterceptors(nil, maximumBody)
	if err != nil {
		t.Fatal(err)
	}
	live, err := NewLiveInterception(maximumBody, 10)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(live.Close)
	handler, err := NewAPI(APIConfig{
		Authority: authority, Recorder: recorder, RepeatClient: client,
		Interceptors: interceptors, Live: live, MaximumBody: maximumBody,
	})
	if err != nil {
		t.Fatal(err)
	}
	return authority, interceptors, live, handler
}

func proxyJSONRequest(t *testing.T, method, endpoint string, input any) *http.Response {
	t.Helper()
	data, err := json.Marshal(input)
	if err != nil {
		t.Fatal(err)
	}
	request, err := http.NewRequest(method, endpoint, bytes.NewReader(data))
	if err != nil {
		t.Fatal(err)
	}
	request.Header.Set("Content-Type", "application/json")
	response, err := http.DefaultClient.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	return response
}

func decodeTestResponse(t *testing.T, response *http.Response, status int, destination any) {
	t.Helper()
	defer response.Body.Close()
	if response.StatusCode != status {
		body, _ := io.ReadAll(response.Body)
		t.Fatalf("status = %d, want %d, body = %q", response.StatusCode, status, body)
	}
	if err := json.NewDecoder(response.Body).Decode(destination); err != nil {
		t.Fatal(err)
	}
}
