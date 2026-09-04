package proxy

import (
	"bytes"
	"context"
	"encoding/base64"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

const (
	defaultLiveTimeout = 30 * time.Second
	defaultMaxPending  = 100
)

var (
	// ErrInterceptionNotFound means a pending interception no longer exists.
	ErrInterceptionNotFound = errors.New("pending interception not found")
	// ErrInterceptionDropped means the operator dropped the exchange.
	ErrInterceptionDropped = errors.New("exchange dropped by live interception")
)

// LiveConfig controls which HTTP phases are paused for operator review.
// Disabled or timed-out interceptions continue without modification.
type LiveConfig struct {
	Enabled   bool `json:"enabled"`
	Requests  bool `json:"requests"`
	Responses bool `json:"responses"`
	TimeoutMS int  `json:"timeout_ms"`
}

// PendingInterception is a bounded, detached snapshot of one paused exchange.
// Bodies use base64 so binary traffic round-trips without coercion.
type PendingInterception struct {
	ID         string      `json:"id"`
	Phase      string      `json:"phase"`
	Method     string      `json:"method"`
	URL        string      `json:"url"`
	StatusCode int         `json:"status_code,omitempty"`
	Headers    http.Header `json:"headers"`
	BodyBase64 string      `json:"body_base64"`
	CreatedAt  time.Time   `json:"created_at"`
	ExpiresAt  time.Time   `json:"expires_at"`
}

// InterceptionUpdate contains optional replacements applied before continuing.
// Headers replace the complete header map when present.
type InterceptionUpdate struct {
	Method     *string      `json:"method,omitempty"`
	URL        *string      `json:"url,omitempty"`
	StatusCode *int         `json:"status_code,omitempty"`
	Headers    *http.Header `json:"headers,omitempty"`
	BodyBase64 *string      `json:"body_base64,omitempty"`
}

type interceptionDecision struct {
	drop   bool
	update InterceptionUpdate
}

type pendingInterception struct {
	view     PendingInterception
	decision chan interceptionDecision
}

// LiveInterception coordinates paused traffic independently of HTTP handlers.
type LiveInterception struct {
	maximumBody    int64
	maximumPending int
	nextID         atomic.Uint64

	mu      sync.Mutex
	config  LiveConfig
	pending map[string]*pendingInterception
	closed  bool
}

// NewLiveInterception returns a disabled live interception coordinator.
func NewLiveInterception(maximumBody int64, maximumPending int) (*LiveInterception, error) {
	if maximumBody < 1 {
		return nil, errors.New("live interception maximum body must be positive")
	}
	if maximumPending < 1 {
		maximumPending = defaultMaxPending
	}
	return &LiveInterception{
		maximumBody: maximumBody, maximumPending: maximumPending,
		config:  LiveConfig{TimeoutMS: int(defaultLiveTimeout / time.Millisecond)},
		pending: make(map[string]*pendingInterception),
	}, nil
}

// Config returns the active live interception settings.
func (i *LiveInterception) Config() LiveConfig {
	i.mu.Lock()
	defer i.mu.Unlock()
	return i.config
}

// Configure atomically changes live interception. Disabling a phase releases
// exchanges already waiting in that phase without modification.
func (i *LiveInterception) Configure(config LiveConfig) error {
	if config.TimeoutMS == 0 {
		config.TimeoutMS = int(defaultLiveTimeout / time.Millisecond)
	}
	if config.TimeoutMS < 100 || config.TimeoutMS > 300_000 {
		return errors.New("live interception timeout_ms must be between 100 and 300000")
	}
	if config.Enabled && !config.Requests && !config.Responses {
		return errors.New("live interception must enable requests, responses, or both")
	}

	i.mu.Lock()
	if i.closed {
		i.mu.Unlock()
		return errors.New("live interception is closed")
	}
	i.config = config
	var released []*pendingInterception
	for id, item := range i.pending {
		keep := config.Enabled && ((item.view.Phase == "request" && config.Requests) || (item.view.Phase == "response" && config.Responses))
		if !keep {
			delete(i.pending, id)
			released = append(released, item)
		}
	}
	i.mu.Unlock()
	for _, item := range released {
		item.decision <- interceptionDecision{}
	}
	return nil
}

// Pending returns pending interceptions in creation order.
func (i *LiveInterception) Pending() []PendingInterception {
	i.mu.Lock()
	defer i.mu.Unlock()
	result := make([]PendingInterception, 0, len(i.pending))
	for _, item := range i.pending {
		result = append(result, clonePendingInterception(item.view))
	}
	sort.Slice(result, func(left, right int) bool {
		if result[left].CreatedAt.Equal(result[right].CreatedAt) {
			return result[left].ID < result[right].ID
		}
		return result[left].CreatedAt.Before(result[right].CreatedAt)
	})
	return result
}

// Get returns one pending interception.
func (i *LiveInterception) Get(id string) (PendingInterception, error) {
	i.mu.Lock()
	defer i.mu.Unlock()
	item, ok := i.pending[strings.TrimSpace(id)]
	if !ok {
		return PendingInterception{}, ErrInterceptionNotFound
	}
	return clonePendingInterception(item.view), nil
}

// Continue validates optional edits and releases one pending exchange.
func (i *LiveInterception) Continue(id string, update InterceptionUpdate) (PendingInterception, error) {
	return i.resolve(id, interceptionDecision{update: update})
}

// Drop releases one pending exchange without forwarding it.
func (i *LiveInterception) Drop(id string) (PendingInterception, error) {
	return i.resolve(id, interceptionDecision{drop: true})
}

func (i *LiveInterception) resolve(id string, decision interceptionDecision) (PendingInterception, error) {
	i.mu.Lock()
	item, ok := i.pending[strings.TrimSpace(id)]
	if !ok {
		i.mu.Unlock()
		return PendingInterception{}, ErrInterceptionNotFound
	}
	if err := i.validateUpdate(item.view.Phase, decision.update); err != nil {
		i.mu.Unlock()
		return PendingInterception{}, err
	}
	delete(i.pending, item.view.ID)
	i.mu.Unlock()
	item.decision <- decision
	return clonePendingInterception(item.view), nil
}

// Close disables interception and releases every waiter. It is idempotent.
func (i *LiveInterception) Close() {
	i.mu.Lock()
	if i.closed {
		i.mu.Unlock()
		return
	}
	i.closed = true
	i.config.Enabled = false
	released := make([]*pendingInterception, 0, len(i.pending))
	for id, item := range i.pending {
		delete(i.pending, id)
		released = append(released, item)
	}
	i.mu.Unlock()
	for _, item := range released {
		item.decision <- interceptionDecision{}
	}
}

func (i *LiveInterception) interceptRequest(ctx context.Context, request *http.Request) error {
	config, ok := i.phaseConfig("request")
	if !ok {
		return nil
	}
	body, err := readInterceptorBody(request.Body, i.maximumBody)
	if err != nil {
		return fmt.Errorf("live request body: %w", err)
	}
	setRequestBody(request, body)
	view := PendingInterception{
		Phase: "request", Method: request.Method, URL: request.URL.String(),
		Headers: request.Header.Clone(), BodyBase64: base64.StdEncoding.EncodeToString(body),
	}
	decision, err := i.pause(ctx, config, view)
	if err != nil {
		return err
	}
	if decision.drop {
		return ErrInterceptionDropped
	}
	return i.applyRequestUpdate(request, decision.update)
}

func (i *LiveInterception) interceptResponse(ctx context.Context, response *http.Response) error {
	config, ok := i.phaseConfig("response")
	if !ok {
		return nil
	}
	body, err := readInterceptorBody(response.Body, i.maximumBody)
	if err != nil {
		return fmt.Errorf("live response body: %w", err)
	}
	setResponseBody(response, body)
	view := PendingInterception{
		Phase: "response", Method: response.Request.Method, URL: response.Request.URL.String(),
		StatusCode: response.StatusCode, Headers: response.Header.Clone(),
		BodyBase64: base64.StdEncoding.EncodeToString(body),
	}
	decision, err := i.pause(ctx, config, view)
	if err != nil {
		return err
	}
	if decision.drop {
		return ErrInterceptionDropped
	}
	return i.applyResponseUpdate(response, decision.update)
}

func (i *LiveInterception) phaseConfig(phase string) (LiveConfig, bool) {
	i.mu.Lock()
	defer i.mu.Unlock()
	config := i.config
	enabled := !i.closed && config.Enabled && ((phase == "request" && config.Requests) || (phase == "response" && config.Responses))
	return config, enabled
}

func (i *LiveInterception) pause(ctx context.Context, config LiveConfig, view PendingInterception) (interceptionDecision, error) {
	now := time.Now().UTC()
	view.ID = fmt.Sprintf("int_%d", i.nextID.Add(1))
	view.CreatedAt = now
	view.ExpiresAt = now.Add(time.Duration(config.TimeoutMS) * time.Millisecond)
	item := &pendingInterception{view: view, decision: make(chan interceptionDecision, 1)}

	i.mu.Lock()
	phaseEnabled := (view.Phase == "request" && i.config.Requests) || (view.Phase == "response" && i.config.Responses)
	if i.closed || !i.config.Enabled || !phaseEnabled || len(i.pending) >= i.maximumPending {
		i.mu.Unlock()
		return interceptionDecision{}, nil
	}
	i.pending[view.ID] = item
	i.mu.Unlock()

	timer := time.NewTimer(time.Until(view.ExpiresAt))
	defer timer.Stop()
	select {
	case decision := <-item.decision:
		return decision, nil
	case <-timer.C:
		if i.removePending(item) {
			return interceptionDecision{}, nil
		}
		return <-item.decision, nil
	case <-ctx.Done():
		i.removePending(item)
		return interceptionDecision{}, ctx.Err()
	}
}

func (i *LiveInterception) removePending(item *pendingInterception) bool {
	i.mu.Lock()
	removed := i.pending[item.view.ID] == item
	if removed {
		delete(i.pending, item.view.ID)
	}
	i.mu.Unlock()
	return removed
}

func (i *LiveInterception) validateUpdate(phase string, update InterceptionUpdate) error {
	if phase == "request" && update.StatusCode != nil {
		return errors.New("request interception cannot set status_code")
	}
	if phase == "response" && (update.Method != nil || update.URL != nil) {
		return errors.New("response interception cannot set method or URL")
	}
	if update.Method != nil {
		method := strings.ToUpper(strings.TrimSpace(*update.Method))
		if !validHeaderName(method) || method == http.MethodConnect {
			return fmt.Errorf("unsupported interception method %q", method)
		}
	}
	if update.URL != nil {
		parsed, err := url.Parse(strings.TrimSpace(*update.URL))
		if err != nil || parsed.Host == "" || (parsed.Scheme != "http" && parsed.Scheme != "https") {
			return fmt.Errorf("invalid interception URL %q", *update.URL)
		}
	}
	if update.StatusCode != nil && (*update.StatusCode < 100 || *update.StatusCode > 599) {
		return errors.New("interception status_code must be between 100 and 599")
	}
	if update.Headers != nil {
		if err := validateLiveHeaders(*update.Headers); err != nil {
			return err
		}
	}
	if update.BodyBase64 != nil {
		body, err := base64.StdEncoding.DecodeString(*update.BodyBase64)
		if err != nil {
			return errors.New("interception body_base64 is invalid")
		}
		if int64(len(body)) > i.maximumBody {
			return fmt.Errorf("interception body exceeds %d bytes", i.maximumBody)
		}
	}
	return nil
}

func (i *LiveInterception) applyRequestUpdate(request *http.Request, update InterceptionUpdate) error {
	if update.Method != nil {
		request.Method = strings.ToUpper(strings.TrimSpace(*update.Method))
	}
	if update.URL != nil {
		parsed, _ := url.Parse(strings.TrimSpace(*update.URL))
		request.URL = parsed
		request.Host = parsed.Host
	}
	if update.Headers != nil {
		request.Header = update.Headers.Clone()
		request.Header.Del("Transfer-Encoding")
		request.Header.Set("Content-Length", fmt.Sprint(request.ContentLength))
		request.TransferEncoding = nil
	}
	if update.BodyBase64 != nil {
		body, _ := base64.StdEncoding.DecodeString(*update.BodyBase64)
		setRequestBody(request, body)
	}
	return nil
}

func (i *LiveInterception) applyResponseUpdate(response *http.Response, update InterceptionUpdate) error {
	if update.StatusCode != nil {
		response.StatusCode = *update.StatusCode
		response.Status = fmt.Sprintf("%d %s", response.StatusCode, http.StatusText(response.StatusCode))
	}
	if update.Headers != nil {
		response.Header = update.Headers.Clone()
		response.Header.Del("Transfer-Encoding")
		response.Header.Set("Content-Length", fmt.Sprint(response.ContentLength))
		response.TransferEncoding = nil
	}
	if update.BodyBase64 != nil {
		body, _ := base64.StdEncoding.DecodeString(*update.BodyBase64)
		setResponseBody(response, body)
	}
	return nil
}

func validateLiveHeaders(headers http.Header) error {
	if len(headers) > 200 {
		return errors.New("interception has more than 200 headers")
	}
	for name, values := range headers {
		if !validHeaderName(name) {
			return fmt.Errorf("invalid interception header %q", name)
		}
		if len(values) > 100 {
			return fmt.Errorf("interception header %q has too many values", name)
		}
		for _, value := range values {
			if strings.ContainsAny(value, "\r\n") {
				return fmt.Errorf("invalid interception header %q", name)
			}
		}
	}
	return nil
}

func setResponseBody(response *http.Response, body []byte) {
	copyBody := append([]byte(nil), body...)
	response.Body = io.NopCloser(bytes.NewReader(copyBody))
	response.ContentLength = int64(len(copyBody))
	if response.Header == nil {
		response.Header = make(http.Header)
	}
	response.Header.Set("Content-Length", fmt.Sprint(len(copyBody)))
	response.Header.Del("Content-MD5")
	response.Header.Del("ETag")
	response.TransferEncoding = nil
}

func clonePendingInterception(item PendingInterception) PendingInterception {
	item.Headers = item.Headers.Clone()
	return item
}
