package proxy

import (
	"github.com/owtf/owtf/internal/har"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestAttachmentSnapshotsOwnership(t *testing.T) {
	var destinations []string
	a := NewAttachment(func(string) error { return nil }, func(target string, _ har.Transaction) error { destinations = append(destinations, target); return nil })
	configure := func(target string) {
		request := httptest.NewRequest(http.MethodPut, "/api/v2/capture", strings.NewReader(`{"target_id":"`+target+`"}`))
		request.Header.Set("Content-Type", "application/json")
		response := httptest.NewRecorder()
		a.ServeHTTP(response, request)
		if response.Code != 200 {
			t.Fatalf("configure: %s", response.Body.String())
		}
	}
	if a.Snapshot() != nil {
		t.Fatal("attachment should start disabled")
	}
	configure("first")
	first := a.Snapshot()
	configure("second")
	second := a.Snapshot()
	configure("")
	if err := first(har.Transaction{}); err != nil {
		t.Fatal(err)
	}
	if err := second(har.Transaction{}); err != nil {
		t.Fatal(err)
	}
	if strings.Join(destinations, ",") != "first,second" {
		t.Fatalf("in-flight ownership changed: %v", destinations)
	}
	if a.Snapshot() != nil {
		t.Fatal("stop did not disable attachment")
	}
}
