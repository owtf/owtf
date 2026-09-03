package proxy

import (
	"context"
	"errors"
	"io"
	"net/http"
	"time"
)

// RetryTransport retries transport failures and the timeout statuses used by
// the historical OWTF proxy. Request bodies are retried only when replayable.
type RetryTransport struct {
	Next        http.RoundTripper
	MaxAttempts int
	Delay       time.Duration
}

// RoundTrip implements http.RoundTripper.
func (t RetryTransport) RoundTrip(request *http.Request) (*http.Response, error) {
	next := t.Next
	if next == nil {
		next = http.DefaultTransport
	}
	attempts := t.MaxAttempts
	if attempts < 1 {
		attempts = 1
	}
	for attempt := 1; ; attempt++ {
		current, err := requestForAttempt(request, attempt)
		if err != nil {
			return nil, err
		}
		response, roundTripErr := next.RoundTrip(current)
		if response == nil && roundTripErr == nil {
			roundTripErr = errors.New("proxy transport returned no response")
		}
		if attempt >= attempts || !retryable(request, response, roundTripErr) {
			return response, roundTripErr
		}
		if response != nil && response.Body != nil {
			_, _ = io.Copy(io.Discard, io.LimitReader(response.Body, 4<<10))
			response.Body.Close()
		}
		if err := waitForRetry(request.Context(), t.Delay); err != nil {
			return nil, err
		}
	}
}

func requestForAttempt(request *http.Request, attempt int) (*http.Request, error) {
	copy := request.Clone(request.Context())
	if attempt == 1 || request.Body == nil {
		copy.Body = request.Body
		return copy, nil
	}
	body, err := request.GetBody()
	if err != nil {
		return nil, err
	}
	copy.Body = body
	return copy, nil
}

func retryable(request *http.Request, response *http.Response, err error) bool {
	if request.Context().Err() != nil {
		return false
	}
	if request.Body != nil && request.GetBody == nil {
		return false
	}
	return err != nil || response == nil || response.StatusCode == http.StatusRequestTimeout || response.StatusCode == 599
}

func waitForRetry(ctx context.Context, delay time.Duration) error {
	if delay <= 0 {
		return nil
	}
	timer := time.NewTimer(delay)
	defer timer.Stop()
	select {
	case <-timer.C:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}
