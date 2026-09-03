package proxy

import (
	"testing"

	"github.com/owtf/owtf/internal/har"
)

func TestRecorderHistoryStatsAndClear(t *testing.T) {
	recorder := NewRecorder(3)
	first := har.Transaction{
		Method: "GET", URL: "https://example.test/one", StatusCode: 200,
		ResponseBody: []byte("public"),
	}
	second := har.Transaction{
		Method: "POST", URL: "https://example.test/two", StatusCode: 404,
		RequestBody: []byte("needle"), ResponseBody: []byte("missing"),
	}
	if err := recorder.Record(first); err != nil {
		t.Fatal(err)
	}
	if err := recorder.Record(second); err != nil {
		t.Fatal(err)
	}
	first.ResponseBody[0] = 'X'

	history := recorder.History(TransactionFilter{Method: "post", Search: "NEEDLE", Limit: 1})
	if len(history) != 1 || history[0].ID != 2 || history[0].Transaction.URL != second.URL {
		t.Fatalf("history = %+v", history)
	}
	all := recorder.Transactions()
	if string(all[0].ResponseBody) != "public" {
		t.Fatalf("recorder retained caller-owned body: %q", all[0].ResponseBody)
	}
	all[0].ResponseBody[0] = 'Y'
	if got := string(recorder.Transactions()[0].ResponseBody); got != "public" {
		t.Fatalf("recorder returned mutable body: %q", got)
	}
	stats := recorder.Stats()
	if stats.Total != 2 || stats.Methods["GET"] != 1 || stats.Statuses[404] != 1 {
		t.Fatalf("stats = %+v", stats)
	}
	if removed := recorder.Clear(); removed != 2 || recorder.Stats().Total != 0 {
		t.Fatalf("removed = %d, stats = %+v", removed, recorder.Stats())
	}
	if err := recorder.Record(first); err != nil {
		t.Fatal(err)
	}
	afterClear := recorder.History(TransactionFilter{})
	if len(afterClear) != 1 || afterClear[0].ID != 3 {
		t.Fatalf("IDs were reused after clear: %+v", afterClear)
	}
}

func TestRecorderHonorsBoundAndPagination(t *testing.T) {
	recorder := NewRecorder(2)
	for index := 0; index < 2; index++ {
		if err := recorder.Record(har.Transaction{Method: "GET", URL: "https://example.test", StatusCode: 200}); err != nil {
			t.Fatal(err)
		}
	}
	if err := recorder.Record(har.Transaction{}); err == nil {
		t.Fatal("recorder exceeded its bound")
	}
	history := recorder.History(TransactionFilter{Offset: 1, Limit: 1})
	if len(history) != 1 || history[0].ID != 2 {
		t.Fatalf("history = %+v", history)
	}
}
