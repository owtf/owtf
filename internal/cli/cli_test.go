package cli

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestOperatorCommandsUseHTTPAPI(t *testing.T) {
	requests := make(map[string]int)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		key := r.Method + " " + r.URL.Path
		requests[key]++
		w.Header().Set("Content-Type", "application/json")
		switch key {
		case "GET /debug/health":
			writeTestJSON(t, w, map[string]string{"status": "ok"})
		case "GET /api/v2/sessions":
			writeTestJSON(t, w, []map[string]any{{"id": "ses_1", "name": "Default session", "created_at": time.Now()}})
		case "POST /api/v2/sessions":
			assertBodyField(t, r, "name", "CLI session")
			w.WriteHeader(http.StatusCreated)
			writeTestJSON(t, w, map[string]any{"id": "ses_1", "name": "CLI session", "created_at": time.Now()})
		case "GET /api/v2/sessions/ses_1":
			writeTestJSON(t, w, map[string]any{"id": "ses_1", "name": "CLI session", "created_at": time.Now()})
		case "POST /api/v2/sessions/ses_1/targets":
			writeTestJSON(t, w, map[string]any{
				"created": []map[string]any{testTarget()}, "duplicates": []string{}, "invalid": []any{},
			})
		case "GET /api/v2/sessions/ses_1/targets":
			writeTestJSON(t, w, []map[string]any{testTarget()})
		case "GET /api/v2/targets/tgt_1":
			writeTestJSON(t, w, testTarget())
		case "DELETE /api/v2/targets/tgt_1":
			w.WriteHeader(http.StatusNoContent)
		case "GET /api/v2/targets/tgt_1/report":
			writeTestJSON(t, w, map[string]any{"target": testTarget(), "tasks": []any{}})
		case "GET /api/v2/plugins":
			writeTestJSON(t, w, []map[string]string{{"id": "OWTF-WSP-001-active"}})
		case "POST /api/v2/runs":
			var input struct {
				SessionID string   `json:"session_id"`
				TargetIDs []string `json:"target_ids"`
				PluginIDs []string `json:"plugin_ids"`
			}
			decodeTestJSON(t, r, &input)
			if input.SessionID != "ses_1" || len(input.TargetIDs) != 1 || input.TargetIDs[0] != "tgt_1" ||
				len(input.PluginIDs) != 1 || input.PluginIDs[0] != "OWTF-WSP-001-active" {
				t.Fatalf("unexpected run request: %+v", input)
			}
			w.WriteHeader(http.StatusAccepted)
			writeTestJSON(t, w, map[string]any{"run": map[string]string{"id": "run_1"}, "tasks": []map[string]string{{"id": "tsk_1"}}})
		case "GET /api/v2/tasks":
			if r.URL.Query().Get("session_id") != "ses_1" || r.URL.Query().Get("status") != "queued" {
				t.Fatalf("unexpected worklist query: %s", r.URL.RawQuery)
			}
			writeTestJSON(t, w, []map[string]string{{"id": "tsk_1", "status": "queued"}})
		case "GET /api/v2/workers":
			writeTestJSON(t, w, []map[string]string{{"id": "worker-1", "status": "idle"}})
		case "GET /api/v2/tasks/tsk_1":
			writeTestJSON(t, w, map[string]string{"id": "tsk_1", "status": "running"})
		case "GET /api/v2/tasks/tsk_1/events":
			writeTestJSON(t, w, []map[string]string{{"task_id": "tsk_1", "message": "task started"}})
		case "POST /api/v2/tasks/tsk_1/cancel":
			writeTestJSON(t, w, map[string]string{"id": "tsk_1", "status": "cancelled"})
		case "GET /api/v2/transactions":
			if r.URL.Query().Get("session_id") != "ses_1" || r.URL.Query().Get("target_id") != "tgt_1" {
				t.Fatalf("unexpected transaction query: %s", r.URL.RawQuery)
			}
			writeTestJSON(t, w, []map[string]any{{"id": "txn_1", "status_code": 200}})
		case "GET /api/v2/artifacts/art_1":
			w.Header().Set("Content-Type", "text/plain")
			_, _ = io.WriteString(w, "captured evidence")
		default:
			http.Error(w, `{"error":"unexpected test route"}`, http.StatusNotFound)
		}
	}))
	defer server.Close()

	jsonCommands := [][]string{
		{"health"},
		{"sessions", "list"},
		{"sessions", "create", "--name", "CLI session"},
		{"sessions", "show", "ses_1"},
		{"targets", "list", "--session", "ses_1"},
		{"targets", "add", "--session", "ses_1", "https://example.test/"},
		{"targets", "show", "tgt_1"},
		{"targets", "report", "tgt_1"},
		{"targets", "delete", "tgt_1"},
		{"plugins", "list"},
		{"runs", "create", "--session", "ses_1", "--target", "tgt_1", "--plugin", "OWTF-WSP-001-active"},
		{"scan", "--session", "ses_1", "--plugin", "OWTF-WSP-001-active", "https://example.test/"},
		{"worklist", "--session", "ses_1", "--status", "queued"},
		{"workers"},
		{"tasks", "show", "tsk_1"},
		{"tasks", "logs", "tsk_1"},
		{"tasks", "cancel", "tsk_1"},
		{"transactions", "list", "--session", "ses_1", "--target", "tgt_1"},
	}
	for _, command := range jsonCommands {
		t.Run(strings.Join(command, " "), func(t *testing.T) {
			var output, errors bytes.Buffer
			args := append([]string{"--url", server.URL}, command...)
			if err := Run(context.Background(), args, &output, &errors); err != nil {
				t.Fatalf("Run() error = %v, stderr = %s", err, errors.String())
			}
			var value any
			if err := json.Unmarshal(output.Bytes(), &value); err != nil {
				t.Fatalf("output is not JSON: %q: %v", output.String(), err)
			}
		})
	}

	artifactPath := filepath.Join(t.TempDir(), "evidence", "body.txt")
	if err := Run(context.Background(), []string{"--url", server.URL, "artifacts", "get", "--output", artifactPath, "art_1"}, io.Discard, io.Discard); err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(artifactPath)
	if err != nil {
		t.Fatal(err)
	}
	if string(data) != "captured evidence" {
		t.Fatalf("unexpected artifact: %q", data)
	}

	for _, route := range []string{
		"GET /debug/health", "GET /api/v2/sessions", "POST /api/v2/sessions",
		"POST /api/v2/sessions/ses_1/targets", "GET /api/v2/sessions/ses_1/targets",
		"POST /api/v2/runs", "GET /api/v2/tasks", "GET /api/v2/workers",
		"GET /api/v2/tasks/tsk_1/events", "POST /api/v2/tasks/tsk_1/cancel",
		"GET /api/v2/transactions", "GET /api/v2/artifacts/art_1",
	} {
		if requests[route] == 0 {
			t.Errorf("CLI did not call %s", route)
		}
	}
}

func TestAPIErrorIsReturned(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		_, _ = io.WriteString(w, `{"error":"not found"}`)
	}))
	defer server.Close()

	err := Run(context.Background(), []string{"--url", server.URL, "targets", "show", "missing"}, io.Discard, io.Discard)
	if err == nil || !strings.Contains(err.Error(), "not found") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func testTarget() map[string]any {
	return map[string]any{
		"id": "tgt_1", "session_id": "ses_1", "kind": "url", "original": "https://example.test/",
		"value": "https://example.test/", "created_at": time.Now(),
	}
}

func assertBodyField(t *testing.T, request *http.Request, key, want string) {
	t.Helper()
	var body map[string]any
	decodeTestJSON(t, request, &body)
	if body[key] != want {
		t.Fatalf("%s = %#v, want %q", key, body[key], want)
	}
}

func decodeTestJSON(t *testing.T, request *http.Request, destination any) {
	t.Helper()
	if err := json.NewDecoder(request.Body).Decode(destination); err != nil {
		t.Fatal(err)
	}
}

func writeTestJSON(t *testing.T, writer http.ResponseWriter, value any) {
	t.Helper()
	if err := json.NewEncoder(writer).Encode(value); err != nil {
		t.Fatal(err)
	}
}
