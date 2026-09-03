package plugin

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/owtf/owtf/internal/model"
)

type transactionReaderFunc func(context.Context, TransactionParts, func(CapturedTransaction) error) error

func (function transactionReaderFunc) Range(ctx context.Context, parts TransactionParts, visit func(CapturedTransaction) error) error {
	return function(ctx, parts, visit)
}

func TestGrepExecutorMatchesHeadersAndBodies(t *testing.T) {
	catalog, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(grepManifest())}})
	if err != nil {
		t.Fatal(err)
	}
	entry, ok := catalog.Get("OWTF-TEST-001-grep")
	if !ok || entry.Availability != "ready" || entry.Executor == nil {
		t.Fatalf("grep plugin is not ready: %+v", entry)
	}

	reader := transactionReaderFunc(func(_ context.Context, parts TransactionParts, visit func(CapturedTransaction) error) error {
		if parts.RequestBody || !parts.ResponseBody {
			t.Fatalf("unexpected requested parts: %+v", parts)
		}
		for _, transaction := range []CapturedTransaction{
			{
				Transaction:  model.Transaction{ID: "txn_2", ResponseHeaders: `{"Server":["Caddy"]}`},
				ResponseBody: []byte(`<meta name="generator" content="Example CMS">`),
			},
			{Transaction: model.Transaction{ID: "txn_1", ResponseHeaders: `{}`}, ResponseBody: []byte("plain")},
		} {
			if err := visit(transaction); err != nil {
				return err
			}
		}
		return nil
	})
	var logs []string
	result, err := entry.Executor(context.Background(), Request{
		Target: model.Target{Kind: "url"}, Transactions: reader,
		Log: func(_, message string) { logs = append(logs, message) },
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Observations) != 2 || len(result.Transactions) != 0 || len(result.Artifacts) != 0 || len(result.Findings) != 0 {
		t.Fatalf("unexpected grep result: %+v", result)
	}
	for _, observation := range result.Observations {
		if observation.Kind != model.ObservationKindGrepMatches || observation.TechniqueCode != "OWTF-TEST-001" {
			t.Fatalf("unexpected observation: %+v", observation)
		}
		var output model.GrepOutput
		if err := json.Unmarshal([]byte(observation.Data), &output); err != nil {
			t.Fatal(err)
		}
		if len(output.TransactionIDs) != 1 || output.TransactionIDs[0] != "txn_2" || output.Truncated {
			t.Fatalf("unexpected grep output: %+v", output)
		}
	}
	if len(logs) != 1 || !strings.Contains(logs[0], "2 matches") {
		t.Fatalf("unexpected logs: %v", logs)
	}
}

func TestGrepExecutorBoundsMatchesAndPropagatesReaderErrors(t *testing.T) {
	manifest := strings.Replace(grepManifest(), "maxMatches: 10", "maxMatches: 1", 1)
	catalog, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(manifest)}})
	if err != nil {
		t.Fatal(err)
	}
	entry, _ := catalog.Get("OWTF-TEST-001-grep")
	reader := transactionReaderFunc(func(_ context.Context, _ TransactionParts, visit func(CapturedTransaction) error) error {
		for _, id := range []string{"txn_2", "txn_1"} {
			if err := visit(CapturedTransaction{
				Transaction:  model.Transaction{ID: id, ResponseHeaders: `{"Server":["Caddy"]}`},
				ResponseBody: []byte(`<meta name="generator">`),
			}); err != nil {
				return err
			}
		}
		return nil
	})
	result, err := entry.Executor(context.Background(), Request{
		Target: model.Target{Kind: "url"}, Transactions: reader, Log: func(string, string) {},
	})
	if err != nil {
		t.Fatal(err)
	}
	for _, observation := range result.Observations {
		var output model.GrepOutput
		if err := json.Unmarshal([]byte(observation.Data), &output); err != nil {
			t.Fatal(err)
		}
		if len(output.TransactionIDs) != 1 || !output.Truncated {
			t.Fatalf("grep output was not bounded: %+v", output)
		}
	}

	want := errors.New("read failed")
	reader = transactionReaderFunc(func(context.Context, TransactionParts, func(CapturedTransaction) error) error { return want })
	_, err = entry.Executor(context.Background(), Request{
		Target: model.Target{Kind: "url"}, Transactions: reader, Log: func(string, string) {},
	})
	if !errors.Is(err, want) {
		t.Fatalf("reader error = %v, want %v", err, want)
	}

	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, err = entry.Executor(ctx, Request{
		Target: model.Target{Kind: "url"}, Transactions: reader, Log: func(string, string) {},
	})
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("cancelled execution error = %v", err)
	}
}

func TestGrepManifestValidation(t *testing.T) {
	valid := grepManifest()
	for name, manifest := range map[string]string{
		"missing rules":       strings.Replace(valid, "      rules:\n", "      rules: []\n", 1),
		"invalid max matches": strings.Replace(valid, "maxMatches: 10", "maxMatches: 1001", 1),
		"duplicate rule":      strings.Replace(valid, "      rules:\n", "      rules:\n        - id: server-header\n          title: Duplicate\n          source: url\n          pattern: example\n", 1),
		"invalid rule ID":     strings.Replace(valid, "id: server-header", "id: Server.Header", 1),
		"unknown source":      strings.Replace(valid, "source: response_headers", "source: database", 1),
		"invalid regexp":      strings.Replace(valid, "(?i)server", "[", 1),
		"command requirement": strings.Replace(valid, "  runtime:\n", "  requirements:\n    commands: [grep]\n  runtime:\n", 1),
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(manifest)}}); err == nil {
				t.Fatal("invalid grep manifest was accepted")
			}
		})
	}
}

func grepManifest() string {
	return `apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-TEST-001-grep
  version: 0.1.0
  title: Grep test
spec:
  techniques: [OWTF-TEST-001]
  group: web
  type: grep
  targetKinds: [url]
  runtime:
    type: grep
    grep:
      maxMatches: 10
      rules:
        - id: server-header
          title: Server header
          source: response_headers
          pattern: (?i)server
        - id: generator-meta
          title: Generator metadata
          source: response_body
          pattern: (?i)<meta[^>]+name=["']generator["']
`
}
