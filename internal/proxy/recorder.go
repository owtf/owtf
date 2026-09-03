package proxy

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"

	"github.com/owtf/owtf/internal/har"
)

// Recorder retains a bounded set of proxy transactions for HAR export.
type Recorder struct {
	mu           sync.RWMutex
	maximum      int
	nextID       uint64
	transactions []CapturedTransaction
}

// CapturedTransaction gives a transaction a stable identifier for the life of
// one proxy process.
type CapturedTransaction struct {
	ID          uint64
	Transaction har.Transaction
}

// TransactionFilter selects captured proxy transactions.
type TransactionFilter struct {
	Method      string
	Status      int
	URLContains string
	Search      string
	Offset      int
	Limit       int
}

// TransactionStats summarizes the current bounded capture.
type TransactionStats struct {
	Total    int
	Methods  map[string]int
	Statuses map[int]int
}

// NewRecorder creates an in-memory recorder. The bound prevents an unattended
// proxy from growing without limit.
func NewRecorder(maximum int) *Recorder {
	if maximum < 1 || maximum > har.MaxEntries {
		maximum = har.MaxEntries
	}
	return &Recorder{maximum: maximum, transactions: make([]CapturedTransaction, 0)}
}

// Record appends one transaction or returns an error at the configured bound.
func (r *Recorder) Record(transaction har.Transaction) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	if len(r.transactions) >= r.maximum {
		return fmt.Errorf("proxy transaction limit %d reached", r.maximum)
	}
	r.nextID++
	r.transactions = append(r.transactions, CapturedTransaction{
		ID: r.nextID, Transaction: cloneTransaction(transaction),
	})
	return nil
}

// Transactions returns a copy of all captured transactions in arrival order.
func (r *Recorder) Transactions() []har.Transaction {
	r.mu.RLock()
	defer r.mu.RUnlock()
	transactions := make([]har.Transaction, len(r.transactions))
	for index, captured := range r.transactions {
		transactions[index] = cloneTransaction(captured.Transaction)
	}
	return transactions
}

// History returns matching captures in arrival order.
func (r *Recorder) History(filter TransactionFilter) []CapturedTransaction {
	r.mu.RLock()
	defer r.mu.RUnlock()
	method := strings.ToUpper(strings.TrimSpace(filter.Method))
	urlText := []byte(filter.URLContains)
	search := []byte(filter.Search)
	result := make([]CapturedTransaction, 0)
	skipped := 0
	for _, captured := range r.transactions {
		transaction := captured.Transaction
		if method != "" && !strings.EqualFold(transaction.Method, method) {
			continue
		}
		if filter.Status != 0 && transaction.StatusCode != filter.Status {
			continue
		}
		if len(urlText) > 0 && !containsFoldASCII([]byte(transaction.URL), urlText) {
			continue
		}
		if len(search) > 0 && !transactionContains(transaction, search) {
			continue
		}
		if skipped < filter.Offset {
			skipped++
			continue
		}
		result = append(result, CapturedTransaction{ID: captured.ID, Transaction: cloneTransaction(transaction)})
		if filter.Limit > 0 && len(result) == filter.Limit {
			break
		}
	}
	return result
}

// Transaction returns one captured transaction by its process-local ID.
func (r *Recorder) Transaction(id uint64) (CapturedTransaction, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	for _, captured := range r.transactions {
		if captured.ID == id {
			captured.Transaction = cloneTransaction(captured.Transaction)
			return captured, true
		}
	}
	return CapturedTransaction{}, false
}

// Stats returns counts for the current capture.
func (r *Recorder) Stats() TransactionStats {
	r.mu.RLock()
	defer r.mu.RUnlock()
	stats := TransactionStats{
		Total: len(r.transactions), Methods: make(map[string]int), Statuses: make(map[int]int),
	}
	for _, captured := range r.transactions {
		stats.Methods[captured.Transaction.Method]++
		stats.Statuses[captured.Transaction.StatusCode]++
	}
	return stats
}

// Clear discards all captures and returns the number removed. IDs are not
// reused, so clients cannot confuse a later transaction with a deleted one.
func (r *Recorder) Clear() int {
	r.mu.Lock()
	defer r.mu.Unlock()
	count := len(r.transactions)
	r.transactions = nil
	return count
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

func cloneTransaction(transaction har.Transaction) har.Transaction {
	transaction.RequestBody = append([]byte(nil), transaction.RequestBody...)
	transaction.ResponseBody = append([]byte(nil), transaction.ResponseBody...)
	return transaction
}

func transactionContains(transaction har.Transaction, search []byte) bool {
	for _, value := range [][]byte{
		[]byte(transaction.Method), []byte(transaction.URL), []byte(transaction.RequestHeaders), transaction.RequestBody,
		[]byte(fmt.Sprint(transaction.StatusCode)), []byte(transaction.ResponseHeaders), transaction.ResponseBody,
	} {
		if containsFoldASCII(value, search) {
			return true
		}
	}
	return false
}

func containsFoldASCII(value, search []byte) bool {
	if len(search) == 0 {
		return true
	}
	for start := 0; start+len(search) <= len(value); start++ {
		matched := true
		for index, want := range search {
			got := value[start+index]
			if got >= 'A' && got <= 'Z' {
				got += 'a' - 'A'
			}
			if want >= 'A' && want <= 'Z' {
				want += 'a' - 'A'
			}
			if got != want {
				matched = false
				break
			}
		}
		if matched {
			return true
		}
	}
	return false
}
