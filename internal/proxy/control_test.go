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

func TestControlServesCAHistoryStatsAndClear(t *testing.T) {
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
	authority, handler := newControlForTest(t, recorder, doerFunc(func(*http.Request) (*http.Response, error) {
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
		t.Fatal("control API returned an invalid CA certificate")
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

func TestControlRepeaterUsesBoundedBinaryBodies(t *testing.T) {
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
	_, handler := newControlForTest(t, NewRecorder(10), repeatClient, 4)
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

func TestControlRejectsInvalidFiltersAndRepeaterRequests(t *testing.T) {
	_, handler := newControlForTest(t, NewRecorder(10), doerFunc(func(*http.Request) (*http.Response, error) {
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

func newControlForTest(t *testing.T, recorder *Recorder, client httpDoer, maximumBody int64) (*Authority, http.Handler) {
	t.Helper()
	directory := t.TempDir()
	authority, err := LoadOrCreateAuthority(filepath.Join(directory, "ca.crt"), filepath.Join(directory, "ca.key"))
	if err != nil {
		t.Fatal(err)
	}
	handler, err := NewControl(ControlConfig{
		Authority: authority, Recorder: recorder, RepeatClient: client, MaximumBody: maximumBody,
	})
	if err != nil {
		t.Fatal(err)
	}
	return authority, handler
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
