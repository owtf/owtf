package api_test

import (
	"archive/zip"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"
	"testing/fstest"
	"time"

	"github.com/owtf/owtf/internal/api"
	"github.com/owtf/owtf/internal/artifact"
	"github.com/owtf/owtf/internal/model"
	"github.com/owtf/owtf/internal/plugin"
	"github.com/owtf/owtf/internal/runner"
	"github.com/owtf/owtf/internal/store"
)

const manifest = `apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-WSP-001-active
  version: 0.1.0
  title: HTTP response collector
  description: Captures one HTTP response as transaction evidence.
spec:
  techniques: [OWTF-WSP-001]
  variant: active
  targetKinds: [url]
  runtime:
    type: builtin
    builtin: http-collector
`

func TestTargetScanPersistsReportAndSupportsDeletion(t *testing.T) {
	targetServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		w.Header().Set("X-OWTF-Evidence", "captured")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte("real response evidence"))
	}))
	defer targetServer.Close()

	tempDir := t.TempDir()
	databasePath := filepath.Join(tempDir, "owtf.db")
	database, err := store.Open(databasePath)
	if err != nil {
		t.Fatal(err)
	}
	artifacts, err := artifact.New(filepath.Join(tempDir, "artifacts"))
	if err != nil {
		t.Fatal(err)
	}
	catalog, err := plugin.Load(fstest.MapFS{"collector/plugin.yaml": &fstest.MapFile{Data: []byte(manifest)}})
	if err != nil {
		t.Fatal(err)
	}
	catalog.RegisterBuiltin("http-collector", plugin.HTTPCollector(targetServer.Client()))
	entries := catalog.Entries()
	if err := database.ReplacePlugins(context.Background(), []model.Plugin{entries[0].Plugin()}); err != nil {
		t.Fatal(err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	taskRunner := runner.New(database, artifacts, catalog, 1, 5*time.Second)
	if err := taskRunner.Start(ctx); err != nil {
		t.Fatal(err)
	}
	server := httptest.NewServer(api.New(database, artifacts, catalog, taskRunner))

	session := requestJSON[model.Session](t, server.Client(), http.MethodPost, server.URL+"/api/v2/sessions", map[string]any{"name": "E2E session"}, http.StatusCreated)
	added := requestJSON[struct {
		Created    []model.Target `json:"created"`
		Duplicates []string       `json:"duplicates"`
		Invalid    []any          `json:"invalid"`
	}](t, server.Client(), http.MethodPost, server.URL+"/api/v2/sessions/"+session.ID+"/targets", map[string]any{
		"targets": []string{targetServer.URL, targetServer.URL + "/", "ftp://invalid.example"},
	}, http.StatusOK)
	if len(added.Created) != 1 || len(added.Duplicates) != 1 || len(added.Invalid) != 1 {
		t.Fatalf("unexpected target intake result: %+v", added)
	}
	target := added.Created[0]

	runResult := requestJSON[struct {
		Run   model.Run    `json:"run"`
		Tasks []model.Task `json:"tasks"`
	}](t, server.Client(), http.MethodPost, server.URL+"/api/v2/runs", map[string]any{
		"session_id": session.ID,
		"target_ids": []string{target.ID},
		"plugin_ids": []string{"OWTF-WSP-001-active"},
	}, http.StatusAccepted)
	if len(runResult.Tasks) != 1 || runResult.Run.Status != model.RunQueued {
		t.Fatalf("unexpected run: %+v", runResult)
	}

	deadline := time.Now().Add(5 * time.Second)
	for {
		tasks := requestJSON[[]model.Task](t, server.Client(), http.MethodGet, server.URL+"/api/v2/tasks?session_id="+session.ID, nil, http.StatusOK)
		if len(tasks) == 1 && tasks[0].Status == model.TaskSucceeded {
			break
		}
		if len(tasks) == 1 && tasks[0].Status == model.TaskFailed {
			t.Fatalf("task failed: %s", tasks[0].Error)
		}
		if time.Now().After(deadline) {
			t.Fatal("timed out waiting for task completion")
		}
		time.Sleep(20 * time.Millisecond)
	}

	report := requestJSON[model.TargetReport](t, server.Client(), http.MethodGet, server.URL+"/api/v2/targets/"+target.ID+"/report", nil, http.StatusOK)
	assertReport(t, report)
	runs := requestJSON[[]model.Run](t, server.Client(), http.MethodGet, server.URL+"/api/v2/runs?session_id="+session.ID, nil, http.StatusOK)
	if len(runs) != 1 || runs[0].ID != runResult.Run.ID || runs[0].Status != model.RunSucceeded {
		t.Fatalf("unexpected run list: %+v", runs)
	}
	storedRun := requestJSON[model.Run](t, server.Client(), http.MethodGet, server.URL+"/api/v2/runs/"+runResult.Run.ID, nil, http.StatusOK)
	if storedRun.Status != model.RunSucceeded || storedRun.FinishedAt == nil {
		t.Fatalf("run was not finalized: %+v", storedRun)
	}
	sessionReport := requestJSON[model.SessionReport](t, server.Client(), http.MethodGet, server.URL+"/api/v2/sessions/"+session.ID+"/report", nil, http.StatusOK)
	if sessionReport.Summary.Targets != 1 || sessionReport.Summary.Runs != 1 || sessionReport.Summary.Tasks != 1 ||
		sessionReport.Summary.Succeeded != 1 || sessionReport.Summary.Transactions != 1 ||
		sessionReport.Summary.Artifacts != 1 || sessionReport.Summary.Observations != 1 {
		t.Fatalf("unexpected session report summary: %+v", sessionReport.Summary)
	}
	assertSessionArchive(t, server.Client(), server.URL+"/api/v2/sessions/"+session.ID+"/export", session.ID)
	transactions := requestJSON[[]model.HTTPExchange](t, server.Client(), http.MethodGet, server.URL+"/api/v2/transactions?session_id="+session.ID, nil, http.StatusOK)
	if len(transactions) != 1 || transactions[0].TargetID != target.ID || transactions[0].StatusCode != http.StatusCreated {
		t.Fatalf("unexpected transaction list: %+v", transactions)
	}
	bodyResponse, err := server.Client().Get(server.URL + "/api/v2/artifacts/" + report.Artifacts[0].ID)
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(bodyResponse.Body)
	bodyResponse.Body.Close()
	if string(body) != "real response evidence" {
		t.Fatalf("unexpected artifact body %q", body)
	}

	server.Close()
	cancel()
	taskRunner.Stop()
	if err := database.Close(); err != nil {
		t.Fatal(err)
	}

	reopened, err := store.Open(databasePath)
	if err != nil {
		t.Fatal(err)
	}
	defer reopened.Close()
	restored, err := reopened.GetTargetReport(context.Background(), target.ID)
	if err != nil {
		t.Fatal(err)
	}
	assertReport(t, restored)
	if err := reopened.DeleteTarget(context.Background(), target.ID); err != nil {
		t.Fatal(err)
	}
	if _, err := reopened.GetTarget(context.Background(), target.ID); !errors.Is(err, store.ErrNotFound) {
		t.Fatalf("deleted target remains available: %v", err)
	}
}

func assertSessionArchive(t *testing.T, client *http.Client, url, sessionID string) {
	t.Helper()
	response, err := client.Get(url)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK || response.Header.Get("Content-Type") != "application/zip" {
		t.Fatalf("unexpected export response: status=%d content-type=%q", response.StatusCode, response.Header.Get("Content-Type"))
	}
	data, err := io.ReadAll(response.Body)
	if err != nil {
		t.Fatal(err)
	}
	archive, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	if err != nil {
		t.Fatal(err)
	}
	files := make(map[string]*zip.File, len(archive.File))
	for _, file := range archive.File {
		files[file.Name] = file
	}
	for _, name := range []string{"report.json", "manifest.json", "index.html"} {
		if files[name] == nil {
			t.Errorf("session export is missing %s", name)
		}
	}
	var exported model.SessionReport
	reportFile, err := files["report.json"].Open()
	if err != nil {
		t.Fatal(err)
	}
	if err := json.NewDecoder(reportFile).Decode(&exported); err != nil {
		reportFile.Close()
		t.Fatal(err)
	}
	reportFile.Close()
	if exported.Session.ID != sessionID || exported.Summary.Artifacts != 1 {
		t.Fatalf("unexpected exported report: %+v", exported)
	}
	if len(archive.File) != 4 {
		t.Fatalf("expected report files plus one artifact, got %d files", len(archive.File))
	}
}

func TestRunRejectsUnsupportedTargetKindBeforeCreatingTasks(t *testing.T) {
	server, database, taskRunner, cancel := newTestServer(t)
	defer func() {
		server.Close()
		cancel()
		taskRunner.Stop()
		database.Close()
	}()

	session := requestJSON[model.Session](t, server.Client(), http.MethodPost, server.URL+"/api/v2/sessions", map[string]any{"name": "Kinds"}, http.StatusCreated)
	added := requestJSON[struct {
		Created []model.Target `json:"created"`
	}](t, server.Client(), http.MethodPost, server.URL+"/api/v2/sessions/"+session.ID+"/targets", map[string]any{
		"targets": []string{"example.test"},
	}, http.StatusOK)
	requestJSON[map[string]any](t, server.Client(), http.MethodPost, server.URL+"/api/v2/runs", map[string]any{
		"session_id": session.ID,
		"target_ids": []string{added.Created[0].ID},
		"plugin_ids": []string{"OWTF-WSP-001-active"},
	}, http.StatusBadRequest)
	tasks := requestJSON[[]model.Task](t, server.Client(), http.MethodGet, server.URL+"/api/v2/tasks?session_id="+session.ID, nil, http.StatusOK)
	if len(tasks) != 0 {
		t.Fatalf("unsupported run created tasks: %+v", tasks)
	}
}

func newTestServer(t *testing.T) (*httptest.Server, *store.Store, *runner.Runner, context.CancelFunc) {
	t.Helper()
	tempDir := t.TempDir()
	database, err := store.Open(filepath.Join(tempDir, "owtf.db"))
	if err != nil {
		t.Fatal(err)
	}
	artifacts, err := artifact.New(filepath.Join(tempDir, "artifacts"))
	if err != nil {
		database.Close()
		t.Fatal(err)
	}
	catalog, err := plugin.Load(fstest.MapFS{"collector/plugin.yaml": &fstest.MapFile{Data: []byte(manifest)}})
	if err != nil {
		database.Close()
		t.Fatal(err)
	}
	catalog.RegisterBuiltin("http-collector", plugin.HTTPCollector(nil))
	entries := catalog.Entries()
	if err := database.ReplacePlugins(context.Background(), []model.Plugin{entries[0].Plugin()}); err != nil {
		database.Close()
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	taskRunner := runner.New(database, artifacts, catalog, 1, 5*time.Second)
	if err := taskRunner.Start(ctx); err != nil {
		cancel()
		database.Close()
		t.Fatal(err)
	}
	return httptest.NewServer(api.New(database, artifacts, catalog, taskRunner)), database, taskRunner, cancel
}

func assertReport(t *testing.T, report model.TargetReport) {
	t.Helper()
	if len(report.Tasks) != 1 || report.Tasks[0].Status != model.TaskSucceeded {
		t.Fatalf("unexpected tasks: %+v", report.Tasks)
	}
	if len(report.Transactions) != 1 || report.Transactions[0].StatusCode != http.StatusCreated {
		t.Fatalf("unexpected transactions: %+v", report.Transactions)
	}
	if len(report.Artifacts) != 1 || len(report.Observations) != 1 {
		t.Fatalf("missing evidence: artifacts=%d observations=%d", len(report.Artifacts), len(report.Observations))
	}
	if len(report.Events) < 3 {
		t.Fatalf("expected lifecycle and plugin logs, got %d events", len(report.Events))
	}
}

func requestJSON[T any](t *testing.T, client *http.Client, method, url string, input any, wantStatus int) T {
	t.Helper()
	var body io.Reader
	if input != nil {
		data, err := json.Marshal(input)
		if err != nil {
			t.Fatal(err)
		}
		body = bytes.NewReader(data)
	}
	request, err := http.NewRequest(method, url, body)
	if err != nil {
		t.Fatal(err)
	}
	if input != nil {
		request.Header.Set("Content-Type", "application/json")
	}
	response, err := client.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	if response.StatusCode != wantStatus {
		data, _ := io.ReadAll(response.Body)
		t.Fatalf("%s %s: got %d, want %d: %s", method, url, response.StatusCode, wantStatus, data)
	}
	var output T
	if err := json.NewDecoder(response.Body).Decode(&output); err != nil {
		t.Fatal(err)
	}
	return output
}
