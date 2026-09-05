package proxy

import (
	"errors"
	"github.com/owtf/owtf/internal/har"
	"net/http"
	"sync"
)

// Attachment routes captures to an explicitly chosen target. Snapshot binds
// ownership before forwarding, rather than when a slow response completes.
type Attachment struct {
	mu        sync.Mutex
	target    string
	lastError string
	validate  func(string) error
	persist   func(string, har.Transaction) error
}

func NewAttachment(validate func(string) error, persist func(string, har.Transaction) error) *Attachment {
	return &Attachment{validate: validate, persist: persist}
}

func (a *Attachment) Snapshot() func(har.Transaction) error {
	if a == nil {
		return nil
	}
	a.mu.Lock()
	target := a.target
	a.mu.Unlock()
	if target == "" {
		return nil
	}
	return func(transaction har.Transaction) error {
		err := a.persist(target, transaction)
		a.mu.Lock()
		if err != nil {
			a.lastError = err.Error()
		}
		a.mu.Unlock()
		return err
	}
}

func (a *Attachment) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if a == nil {
		writeAPIError(w, http.StatusServiceUnavailable, errors.New("capture attachment is not configured"))
		return
	}
	if r.Method == http.MethodPut {
		if !requireAPIJSON(w, r) {
			return
		}
		var input struct {
			Target string `json:"target_id"`
		}
		if err := decodeAPIJSONBounded(r.Body, &input, 4096); err != nil {
			writeAPIError(w, http.StatusBadRequest, err)
			return
		}
		if input.Target != "" {
			if err := a.validate(input.Target); err != nil {
				writeAPIError(w, http.StatusBadRequest, err)
				return
			}
		}
		a.mu.Lock()
		a.target = input.Target
		a.lastError = ""
		a.mu.Unlock()
	}
	a.mu.Lock()
	state := map[string]string{"target_id": a.target, "last_error": a.lastError}
	a.mu.Unlock()
	writeAPIJSON(w, http.StatusOK, state)
}
