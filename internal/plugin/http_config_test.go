package plugin

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"testing/fstest"
	"time"

	"github.com/owtf/owtf/internal/model"
)

func TestConfiguredHTTPCollectors(t *testing.T) {
	catalog, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(httpManifest(`
      probes:
        - name: response
          method: GET
`))}})
	if err != nil {
		t.Fatal(err)
	}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.UserAgent() != "test-agent" {
			t.Errorf("User-Agent = %q", r.UserAgent())
		}
		if r.URL.Query().Has("slow") {
			<-r.Context().Done()
			return
		}
		w.Write([]byte("evidence"))
	}))
	defer server.Close()
	client := server.Client()
	client.Timeout = 40 * time.Millisecond
	catalog.ConfigureHTTP(client, "test-agent")
	entry, _ := catalog.Get("OWTF-TEST-001-semi_passive")
	for name, execute := range map[string]Executor{"manifest": entry.Executor, "baseline": HTTPCollector(client, "test-agent")} {
		t.Run(name, func(t *testing.T) {
			logs := 0
			request := Request{Target: model.Target{Kind: "url", Value: server.URL}, Log: func(string, string) { logs++ }}
			result, err := execute(context.Background(), request)
			if err != nil || len(result.Transactions) != 1 || logs == 0 {
				t.Fatalf("result=%+v logs=%d err=%v", result, logs, err)
			}
			request.Target.Value += "?slow=1"
			_, err = execute(context.Background(), request)
			if !errors.Is(err, context.DeadlineExceeded) {
				t.Fatalf("request timeout: %v", err)
			}
			ctx, cancel := context.WithTimeout(context.Background(), time.Millisecond)
			defer cancel()
			_, err = execute(ctx, request)
			if !errors.Is(err, context.DeadlineExceeded) {
				t.Fatalf("task deadline: %v", err)
			}
		})
	}
}
