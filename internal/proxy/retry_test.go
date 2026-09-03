package proxy

import (
	"errors"
	"io"
	"net/http"
	"strings"
	"testing"
)

func TestRetryTransportRetriesOWTFTimeoutStatuses(t *testing.T) {
	attempts := 0
	transport := RetryTransport{MaxAttempts: 3, Next: roundTripperFunc(func(request *http.Request) (*http.Response, error) {
		attempts++
		status := http.StatusRequestTimeout
		if attempts == 2 {
			status = 599
		}
		if attempts == 3 {
			status = http.StatusOK
		}
		return testResponse(request, status, "attempt"), nil
	})}
	request, _ := http.NewRequest(http.MethodGet, "https://example.test", nil)
	response, err := transport.RoundTrip(request)
	if err != nil {
		t.Fatal(err)
	}
	response.Body.Close()
	if attempts != 3 || response.StatusCode != http.StatusOK {
		t.Fatalf("attempts = %d, status = %d", attempts, response.StatusCode)
	}
}

func TestRetryTransportRetriesReplayableBody(t *testing.T) {
	attempts := 0
	transport := RetryTransport{MaxAttempts: 2, Next: roundTripperFunc(func(request *http.Request) (*http.Response, error) {
		attempts++
		body, _ := io.ReadAll(request.Body)
		if string(body) != "payload" {
			t.Fatalf("attempt %d body = %q", attempts, body)
		}
		if attempts == 1 {
			return nil, errors.New("temporary failure")
		}
		return testResponse(request, http.StatusCreated, "ok"), nil
	})}
	request, _ := http.NewRequest(http.MethodPost, "https://example.test", strings.NewReader("payload"))
	response, err := transport.RoundTrip(request)
	if err != nil {
		t.Fatal(err)
	}
	response.Body.Close()
	if attempts != 2 || response.StatusCode != http.StatusCreated {
		t.Fatalf("attempts = %d, status = %d", attempts, response.StatusCode)
	}
}

func TestRetryTransportRejectsMissingResponse(t *testing.T) {
	transport := RetryTransport{MaxAttempts: 2, Next: roundTripperFunc(func(*http.Request) (*http.Response, error) {
		return nil, nil
	})}
	request, _ := http.NewRequest(http.MethodGet, "https://example.test", nil)
	if _, err := transport.RoundTrip(request); err == nil {
		t.Fatal("missing response was returned as success")
	}
}

func testResponse(request *http.Request, status int, body string) *http.Response {
	return &http.Response{
		Status: http.StatusText(status), StatusCode: status, Proto: "HTTP/1.1", ProtoMajor: 1, ProtoMinor: 1,
		Header: make(http.Header), Body: io.NopCloser(strings.NewReader(body)), ContentLength: int64(len(body)), Request: request,
	}
}

type roundTripperFunc func(*http.Request) (*http.Response, error)

func (function roundTripperFunc) RoundTrip(request *http.Request) (*http.Response, error) {
	return function(request)
}
