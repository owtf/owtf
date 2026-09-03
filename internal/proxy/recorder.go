package proxy

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"

	"github.com/owtf/owtf/internal/har"
)

// Recorder retains a bounded set of proxy transactions for HAR export.
type Recorder struct {
	mu           sync.Mutex
	maximum      int
	transactions []har.Transaction
}

// NewRecorder creates an in-memory recorder. The bound prevents an unattended
// proxy from growing without limit.
func NewRecorder(maximum int) *Recorder {
	if maximum < 1 || maximum > har.MaxEntries {
		maximum = har.MaxEntries
	}
	return &Recorder{maximum: maximum, transactions: make([]har.Transaction, 0)}
}

// Record appends one transaction or returns an error at the configured bound.
func (r *Recorder) Record(transaction har.Transaction) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	if len(r.transactions) >= r.maximum {
		return fmt.Errorf("proxy transaction limit %d reached", r.maximum)
	}
	r.transactions = append(r.transactions, transaction)
	return nil
}

// Transactions returns a copy of all captured transactions in arrival order.
func (r *Recorder) Transactions() []har.Transaction {
	r.mu.Lock()
	defer r.mu.Unlock()
	return append([]har.Transaction(nil), r.transactions...)
}

// WriteHAR atomically writes the current capture as a HAR 1.2 document.
func (r *Recorder) WriteHAR(path string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return fmt.Errorf("create HAR directory: %w", err)
	}
	temporary, err := os.CreateTemp(filepath.Dir(path), ".owtf-proxy-*.har")
	if err != nil {
		return fmt.Errorf("create HAR file: %w", err)
	}
	temporaryPath := temporary.Name()
	defer os.Remove(temporaryPath)
	if err := temporary.Chmod(0o600); err != nil {
		temporary.Close()
		return fmt.Errorf("protect HAR file: %w", err)
	}
	if err := har.Write(temporary, r.Transactions()); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Close(); err != nil {
		return fmt.Errorf("close HAR file: %w", err)
	}
	if err := os.Rename(temporaryPath, path); err != nil {
		return fmt.Errorf("replace HAR file: %w", err)
	}
	return nil
}
