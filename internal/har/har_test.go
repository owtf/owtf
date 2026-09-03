package har

import (
	"bytes"
	"fmt"
	"strings"
	"testing"
	"time"
)

func TestParseTransactions(t *testing.T) {
	input := `{
  "log": {"version":"1.2", "entries":[{
    "startedDateTime":"2026-09-02T10:11:12.123-07:00", "time":12.6,
    "request":{"method":"post", "url":"https://example.test/login", "headers":[
      {"name":"Accept","value":"text/plain"},{"name":"Accept","value":"application/json"}],
      "postData":{"mimeType":"application/json","text":"{\"ok\":true}"}},
    "response":{"status":201, "headers":[{"name":"Content-Type","value":"application/octet-stream"}],
      "content":{"mimeType":"application/octet-stream","text":"AAEC","encoding":"base64"}}
  }]}
}`
	items, err := Parse(strings.NewReader(input))
	if err != nil {
		t.Fatal(err)
	}
	if len(items) != 1 || items[0].Method != "POST" || items[0].StatusCode != 201 || items[0].DurationMS != 13 {
		t.Fatalf("unexpected transaction: %+v", items)
	}
	if string(items[0].RequestBody) != `{"ok":true}` || string(items[0].ResponseBody) != string([]byte{0, 1, 2}) {
		t.Fatalf("unexpected bodies: request=%q response=%v", items[0].RequestBody, items[0].ResponseBody)
	}
	if items[0].RequestHeaders != `{"Accept":["text/plain","application/json"]}` {
		t.Fatalf("duplicate headers were not preserved: %s", items[0].RequestHeaders)
	}
}

func TestParseRejectsInvalidTransactions(t *testing.T) {
	tests := []struct {
		name, entry, want string
	}{
		{"empty", "", "no transactions"},
		{"method", `"startedDateTime":"2026-09-02T10:11:12Z","time":1,"request":{"url":"https://example.test"},"response":{"status":200}`, "method is required"},
		{"url", `"startedDateTime":"2026-09-02T10:11:12Z","time":1,"request":{"method":"GET","url":"file:///tmp/a"},"response":{"status":200}`, "invalid HTTP URL"},
		{"time", `"startedDateTime":"yesterday","time":1,"request":{"method":"GET","url":"https://example.test"},"response":{"status":200}`, "invalid startedDateTime"},
		{"base64", `"startedDateTime":"2026-09-02T10:11:12Z","time":1,"request":{"method":"GET","url":"https://example.test"},"response":{"status":200,"content":{"text":"%%%","encoding":"base64"}}`, "invalid base64"},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			input := `{"log":{"entries":[{` + test.entry + `}]}}`
			if test.entry == "" {
				input = `{"log":{"entries":[]}}`
			}
			_, err := Parse(strings.NewReader(input))
			if err == nil || !strings.Contains(err.Error(), test.want) {
				t.Fatalf("error=%v, want substring %q", err, test.want)
			}
		})
	}
}

func TestParseLimitsTransactionCount(t *testing.T) {
	entry := `{"startedDateTime":"2026-09-02T10:11:12Z","time":1,"request":{"method":"GET","url":"https://example.test"},"response":{"status":200}}`
	input := `{"log":{"entries":[` + strings.Repeat(entry+",", MaxEntries) + entry + `]}}`
	_, err := Parse(strings.NewReader(input))
	if err == nil || !strings.Contains(err.Error(), fmt.Sprintf("maximum is %d", MaxEntries)) {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestWriteRoundTripsBinaryBodiesAndDuplicateHeaders(t *testing.T) {
	original := Transaction{
		Method: "POST", URL: "https://example.test/upload",
		RequestHeaders: `{"X-Test":["one","two"]}`, RequestBody: []byte{0, 1, 2},
		RequestMediaType: "application/octet-stream", StatusCode: 201,
		ResponseHeaders: `{"Content-Type":["application/octet-stream"]}`,
		ResponseBody:    []byte{3, 4, 5}, ResponseMediaType: "application/octet-stream",
		DurationMS: 17, StartedAt: time.Date(2026, 9, 2, 10, 11, 12, 123, time.UTC),
	}
	var output bytes.Buffer
	if err := Write(&output, []Transaction{original}); err != nil {
		t.Fatal(err)
	}
	parsed, err := Parse(&output)
	if err != nil {
		t.Fatal(err)
	}
	if len(parsed) != 1 || !bytes.Equal(parsed[0].RequestBody, original.RequestBody) || !bytes.Equal(parsed[0].ResponseBody, original.ResponseBody) {
		t.Fatalf("HAR round trip changed bodies: %+v", parsed)
	}
	if parsed[0].RequestHeaders != original.RequestHeaders || parsed[0].DurationMS != original.DurationMS {
		t.Fatalf("HAR round trip changed metadata: %+v", parsed[0])
	}
}
