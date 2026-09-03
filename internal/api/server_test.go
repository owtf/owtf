package api_test

import (
	"archive/zip"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"
	"testing/fstest"
	"time"

	"github.com/owtf/owtf/internal/api"
	"github.com/owtf/owtf/internal/artifact"
	"github.com/owtf/owtf/internal/model"
	"github.com/owtf/owtf/internal/plugin"
	"github.com/owtf/owtf/internal/profile"
	"github.com/owtf/owtf/internal/runner"
	"github.com/owtf/owtf/internal/store"
	targetvalue "github.com/owtf/owtf/internal/target"
)

func TestImportBrowseAndDeleteHARTransactions(t *testing.T) {
	tempDir := t.TempDir()
	database, err := store.Open(filepath.Join(tempDir, "owtf.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()
	artifacts, err := artifact.New(filepath.Join(tempDir, "artifacts"))
	if err != nil {
		t.Fatal(err)
	}
	catalog, err := plugin.Load(fstest.MapFS{})
	if err != nil {
		t.Fatal(err)
	}
	taskRunner := runner.New(database, artifacts, catalog, 1, time.Second)
	server := httptest.NewServer(api.New(api.Config{
		Store: database, Artifacts: artifacts, Plugins: catalog, Runner: taskRunner,
	}))
	defer server.Close()

	ctx := context.Background()
	session, _ := database.CreateSession(ctx, "Imported traffic")
	normalized, err := targetvalue.Normalize("https://example.test")
	if err != nil {
		t.Fatal(err)
	}
	added, _ := database.AddTargets(ctx, session.ID, []targetvalue.Normalized{normalized})
	targetID := added.Created[0].ID
	harData := []byte(`{"log":{"version":"1.2","entries":[{
  "startedDateTime":"2026-09-02T10:11:12Z","time":8.4,
  "request":{"method":"POST","url":"https://example.test/submit","headers":[{"name":"X-Test","value":"one"}],"postData":{"mimeType":"text/plain","text":"request body"}},
  "response":{"status":201,"headers":[{"name":"Content-Type","value":"text/plain"}],"content":{"mimeType":"text/plain","text":"response body"}}
}]}}`)

	invalid := importHAR(t, server.Client(), server.URL+"/api/v2/targets/"+targetID+"/transactions/import", "broken.har", []byte(`{"log":`), http.StatusBadRequest)
	if invalid.Imported != 0 {
		t.Fatalf("invalid HAR imported transactions: %+v", invalid)
	}
	result := importHAR(t, server.Client(), server.URL+"/api/v2/targets/"+targetID+"/transactions/import", "../../capture.har", harData, http.StatusCreated)
	if result.Imported != 1 || result.SourceArtifact.Name != "capture.har" || len(result.Transactions) != 1 {
		t.Fatalf("unexpected import result: %+v", result)
	}
	transaction := result.Transactions[0]
	if transaction.TaskID != "" || transaction.RequestBodyArtifactID == "" || transaction.ResponseBodyArtifactID == "" || transaction.SourceArtifactID != result.SourceArtifact.ID {
		t.Fatalf("transaction ownership or files are incorrect: %+v", transaction)
	}
	stored := requestJSON[model.Transaction](t, server.Client(), http.MethodGet,
		server.URL+"/api/v2/targets/"+targetID+"/transactions/"+transaction.ID, nil, http.StatusOK)
	if stored.ID != transaction.ID || stored.StatusCode != http.StatusCreated {
		t.Fatalf("unexpected stored transaction: %+v", stored)
	}
	targetTransactions := requestJSON[[]model.Transaction](t, server.Client(), http.MethodGet,
		server.URL+"/api/v2/targets/"+targetID+"/transactions", nil, http.StatusOK)
	if len(targetTransactions) != 1 || targetTransactions[0].ID != transaction.ID {
		t.Fatalf("unexpected target transactions: %+v", targetTransactions)
	}
	search := requestJSON[model.TransactionSearchResult](t, server.Client(), http.MethodGet,
		server.URL+"/api/v2/transactions/search?session_id="+session.ID+"&target_id="+targetID+"&search=SUBMIT&method=post&status_code=201&limit=1&offset=0", nil, http.StatusOK)
	if search.RecordsTotal != 1 || search.RecordsFiltered != 1 || len(search.Data) != 1 || search.Data[0].ID != transaction.ID {
		t.Fatalf("unexpected transaction search: %+v", search)
	}
	targetSearch := requestJSON[model.TransactionSearchResult](t, server.Client(), http.MethodGet,
		server.URL+"/api/v2/targets/"+targetID+"/transactions/search?search=submit", nil, http.StatusOK)
	if targetSearch.RecordsTotal != 1 || targetSearch.RecordsFiltered != 1 || len(targetSearch.Data) != 1 {
		t.Fatalf("unexpected target transaction search: %+v", targetSearch)
	}
	requestJSON[map[string]string](t, server.Client(), http.MethodGet,
		server.URL+"/api/v2/transactions/search?session_id="+session.ID+"&status_code=99", nil, http.StatusBadRequest)
	requestJSON[map[string]string](t, server.Client(), http.MethodGet,
		server.URL+"/api/v2/targets/"+targetID+"/transactions/search?unknown=true", nil, http.StatusBadRequest)
	for artifactID, want := range map[string]string{
		result.SourceArtifact.ID: string(harData), transaction.RequestBodyArtifactID: "request body",
		transaction.ResponseBodyArtifactID: "response body",
	} {
		response, getErr := server.Client().Get(server.URL + "/api/v2/artifacts/" + artifactID)
		if getErr != nil {
			t.Fatal(getErr)
		}
		body, _ := io.ReadAll(response.Body)
		response.Body.Close()
		if response.StatusCode != http.StatusOK || string(body) != want {
			t.Fatalf("artifact %s: status=%d body=%q", artifactID, response.StatusCode, body)
		}
	}
	report := requestJSON[model.TargetReport](t, server.Client(), http.MethodGet, server.URL+"/api/v2/targets/"+targetID+"/report", nil, http.StatusOK)
	if len(report.Tasks) != 0 || len(report.Transactions) != 1 || len(report.Artifacts) != 3 {
		t.Fatalf("imported target report is incomplete: %+v", report)
	}
	sessionReport := requestJSON[model.SessionReport](t, server.Client(), http.MethodGet, server.URL+"/api/v2/sessions/"+session.ID+"/report", nil, http.StatusOK)
	if sessionReport.Summary.Tasks != 0 || sessionReport.Summary.Transactions != 1 || sessionReport.Summary.Artifacts != 3 {
		t.Fatalf("imported session report is incorrect: %+v", sessionReport.Summary)
	}
	deleteRequest, _ := http.NewRequest(http.MethodDelete,
		server.URL+"/api/v2/targets/"+targetID+"/transactions/"+transaction.ID, nil)
	deleteResponse, err := server.Client().Do(deleteRequest)
	if err != nil {
		t.Fatal(err)
	}
	deleteResponse.Body.Close()
	if deleteResponse.StatusCode != http.StatusNoContent {
		t.Fatalf("delete status=%d, want %d", deleteResponse.StatusCode, http.StatusNoContent)
	}
	report = requestJSON[model.TargetReport](t, server.Client(), http.MethodGet, server.URL+"/api/v2/targets/"+targetID+"/report", nil, http.StatusOK)
	if len(report.Transactions) != 0 || len(report.Artifacts) != 0 {
		t.Fatalf("deleted transaction remains in report: %+v", report)
	}
}

type harImportResult struct {
	Imported       int                 `json:"imported"`
	SourceArtifact model.Artifact      `json:"source_artifact"`
	Transactions   []model.Transaction `json:"transactions"`
}

func importHAR(t *testing.T, client *http.Client, endpoint, filename string, data []byte, status int) harImportResult {
	t.Helper()
	var body bytes.Buffer
	writer := multipart.NewWriter(&body)
	part, err := writer.CreateFormFile("har", filename)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := part.Write(data); err != nil {
		t.Fatal(err)
	}
	if err := writer.Close(); err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodPost, endpoint, &body)
	request.Header.Set("Content-Type", writer.FormDataContentType())
	response, err := client.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	if response.StatusCode != status {
		responseBody, _ := io.ReadAll(response.Body)
		t.Fatalf("import status=%d, want %d: %s", response.StatusCode, status, responseBody)
	}
	var result harImportResult
	if status != http.StatusNoContent {
		_ = json.NewDecoder(response.Body).Decode(&result)
	}
	return result
}

const manifest = `apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-WSP-001-active
  version: 0.1.0
  title: HTTP response collector
  description: Captures one HTTP response as transaction evidence.
spec:
  techniques: [OWTF-WSP-001]
  group: web
  type: active
  targetKinds: [url]
  inputs:
    - name: request_label
      type: string
      default: default
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
	collector := plugin.HTTPCollector(targetServer.Client())
	receivedInputs := make(chan map[string]any, 1)
	catalog.RegisterBuiltin("http-collector", func(ctx context.Context, request plugin.Request) (plugin.Result, error) {
		receivedInputs <- request.Inputs
		return collector(ctx, request)
	})
	entries := catalog.Entries()
	if err := database.ReplacePlugins(context.Background(), []model.Plugin{entries[0].Plugin()}); err != nil {
		t.Fatal(err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	taskRunner := runner.New(database, artifacts, catalog, 1, 5*time.Second)
	if err := taskRunner.Start(ctx); err != nil {
		t.Fatal(err)
	}
	server := httptest.NewServer(api.New(api.Config{
		Store: database, Artifacts: artifacts, Plugins: catalog, Runner: taskRunner,
	}))

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
	plugins := requestJSON[[]model.Plugin](t, server.Client(), http.MethodGet, server.URL+"/api/v2/plugins", nil, http.StatusOK)
	if len(plugins) != 1 || len(plugins[0].Inputs) != 1 || plugins[0].Inputs[0].Name != "request_label" {
		t.Fatalf("plugin inputs are not exposed: %+v", plugins)
	}
	requestJSON[map[string]string](t, server.Client(), http.MethodPost, server.URL+"/api/v2/runs", map[string]any{
		"session_id":    session.ID,
		"target_ids":    []string{target.ID},
		"plugin_ids":    []string{"OWTF-WSP-001-active"},
		"plugin_inputs": map[string]any{"OWTF-WSP-001-active": map[string]any{"unknown": true}},
	}, http.StatusBadRequest)

	runResult := requestJSON[struct {
		Run   model.Run    `json:"run"`
		Tasks []model.Task `json:"tasks"`
	}](t, server.Client(), http.MethodPost, server.URL+"/api/v2/runs", map[string]any{
		"session_id":    session.ID,
		"target_ids":    []string{target.ID},
		"plugin_ids":    []string{"OWTF-WSP-001-active"},
		"plugin_inputs": map[string]any{"OWTF-WSP-001-active": map[string]any{"request_label": "API run"}},
	}, http.StatusAccepted)
	if len(runResult.Tasks) != 1 || runResult.Run.Status != model.RunQueued || runResult.Tasks[0].Inputs["request_label"] != "API run" {
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
	inputs := <-receivedInputs
	if inputs["request_label"] != "API run" {
		t.Fatalf("runner did not use snapshotted inputs: %#v", inputs)
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
	transactions := requestJSON[[]model.Transaction](t, server.Client(), http.MethodGet, server.URL+"/api/v2/transactions?session_id="+session.ID, nil, http.StatusOK)
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

func TestPluginGroupLaunchKeepsUnavailablePluginsInWorklist(t *testing.T) {
	tempDir := t.TempDir()
	database, err := store.Open(filepath.Join(tempDir, "owtf.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()
	artifacts, err := artifact.New(filepath.Join(tempDir, "artifacts"))
	if err != nil {
		t.Fatal(err)
	}
	passive := strings.ReplaceAll(manifest, "OWTF-WSP-001-active", "OWTF-IG-001-passive")
	passive = strings.ReplaceAll(passive, "OWTF-WSP-001", "OWTF-IG-001")
	passive = strings.Replace(passive, "type: active", "type: passive", 1)
	catalog, err := plugin.Load(fstest.MapFS{
		"active/plugin.yaml":  &fstest.MapFile{Data: []byte(manifest)},
		"passive/plugin.yaml": &fstest.MapFile{Data: []byte(passive)},
	})
	if err != nil {
		t.Fatal(err)
	}
	profiles, err := profile.Load(fstest.MapFS{"default.yaml": &fstest.MapFile{Data: []byte(`
apiVersion: owtf.dev/v1alpha1
kind: Profile
metadata: {name: default}
spec:
  plugins:
    - OWTF-WSP-001-active
    - OWTF-IG-001-passive
`)}})
	if err != nil {
		t.Fatal(err)
	}
	if err := profiles.ValidatePlugins(catalog); err != nil {
		t.Fatal(err)
	}
	entries := catalog.Entries()
	plugins := make([]model.Plugin, 0, len(entries))
	for _, entry := range entries {
		plugins = append(plugins, entry.Plugin())
	}
	if err := database.ReplacePlugins(context.Background(), plugins); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	taskRunner := runner.New(database, artifacts, catalog, 1, time.Second)
	if err := taskRunner.Start(ctx); err != nil {
		t.Fatal(err)
	}
	defer taskRunner.Stop()
	server := httptest.NewServer(api.New(api.Config{
		Store: database, Artifacts: artifacts, Plugins: catalog, Profiles: profiles,
		DefaultProfile: "default", Runner: taskRunner,
	}))
	defer server.Close()

	session := requestJSON[model.Session](t, server.Client(), http.MethodPost, server.URL+"/api/v2/sessions", map[string]any{"name": "Group"}, http.StatusCreated)
	added := requestJSON[struct {
		Created []model.Target `json:"created"`
	}](t, server.Client(), http.MethodPost, server.URL+"/api/v2/sessions/"+session.ID+"/targets", map[string]any{"targets": []string{"https://example.test"}}, http.StatusOK)
	requestJSON[map[string]any](t, server.Client(), http.MethodPost, server.URL+"/api/v2/runs", map[string]any{
		"session_id": session.ID, "target_ids": []string{added.Created[0].ID},
		"plugin_group": "web", "profile": "missing",
	}, http.StatusBadRequest)
	requestJSON[map[string]any](t, server.Client(), http.MethodPost, server.URL+"/api/v2/runs", map[string]any{
		"session_id": session.ID, "target_ids": []string{added.Created[0].ID},
		"plugin_ids": []string{"OWTF-WSP-001-active"}, "profile": "default",
	}, http.StatusBadRequest)
	result := requestJSON[struct {
		Run   model.Run    `json:"run"`
		Tasks []model.Task `json:"tasks"`
	}](t, server.Client(), http.MethodPost, server.URL+"/api/v2/runs", map[string]any{
		"session_id": session.ID, "target_ids": []string{added.Created[0].ID}, "plugin_group": "web",
	}, http.StatusAccepted)
	if result.Run.Profile != "default" || result.Run.Status != model.RunBlocked || result.Run.FinishedAt == nil || len(result.Tasks) != 2 {
		t.Fatalf("unexpected blocked group run: %+v", result)
	}
	if result.Tasks[0].PluginID != "OWTF-WSP-001-active" || result.Tasks[1].PluginID != "OWTF-IG-001-passive" {
		t.Fatalf("profile order was not applied: %+v", result.Tasks)
	}
	for _, task := range result.Tasks {
		if task.Status != model.TaskBlocked || !strings.Contains(task.Error, "runtime is not registered") {
			t.Fatalf("unavailable plugin disappeared from worklist: %+v", task)
		}
	}
	filtered := requestJSON[[]model.Plugin](t, server.Client(), http.MethodGet, server.URL+"/api/v2/plugins?group=web&type=passive", nil, http.StatusOK)
	if len(filtered) != 1 || filtered[0].Type != "passive" {
		t.Fatalf("plugin group/type filter failed: %+v", filtered)
	}
	listedProfiles := requestJSON[[]profile.Profile](t, server.Client(), http.MethodGet, server.URL+"/api/v2/profiles", nil, http.StatusOK)
	if len(listedProfiles) != 1 || listedProfiles[0].Name != "default" {
		t.Fatalf("profile list is incorrect: %+v", listedProfiles)
	}
	shownProfile := requestJSON[profile.Profile](t, server.Client(), http.MethodGet, server.URL+"/api/v2/profiles/default", nil, http.StatusOK)
	if len(shownProfile.Plugins) != 2 || shownProfile.Plugins[0] != "OWTF-WSP-001-active" {
		t.Fatalf("profile detail is incorrect: %+v", shownProfile)
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

func TestTargetLifecycleAPI(t *testing.T) {
	server, database, taskRunner, cancel := newTestServer(t)
	defer func() {
		server.Close()
		cancel()
		taskRunner.Stop()
		database.Close()
	}()

	session := requestJSON[model.Session](t, server.Client(), http.MethodPost, server.URL+"/api/v2/sessions", map[string]any{
		"name": "Target review",
	}, http.StatusCreated)
	added := requestJSON[struct {
		Created []model.Target `json:"created"`
	}](t, server.Client(), http.MethodPost, server.URL+"/api/v2/sessions/"+session.ID+"/targets", map[string]any{
		"targets": []string{"https://example.test/one", "https://other.test/", "example.test"},
	}, http.StatusOK)
	if len(added.Created) != 3 || !added.Created[0].Scope {
		t.Fatalf("targets do not default to scope: %+v", added.Created)
	}

	targetID := added.Created[0].ID
	updated := requestJSON[model.Target](t, server.Client(), http.MethodPatch, server.URL+"/api/v2/targets/"+targetID, map[string]any{
		"scope": false,
	}, http.StatusOK)
	if updated.Scope {
		t.Fatalf("target scope was not updated: %+v", updated)
	}
	result := requestJSON[model.TargetSearchResult](t, server.Client(), http.MethodGet,
		server.URL+"/api/v2/sessions/"+session.ID+"/targets/search?search=EXAMPLE&kind=url&scope=false&limit=1&offset=0", nil, http.StatusOK)
	if result.RecordsTotal != 3 || result.RecordsFiltered != 1 || len(result.Data) != 1 || result.Data[0].ID != targetID {
		t.Fatalf("unexpected target search: %+v", result)
	}
	requestJSON[map[string]string](t, server.Client(), http.MethodGet,
		server.URL+"/api/v2/sessions/"+session.ID+"/targets/search?scope=invalid", nil, http.StatusBadRequest)

	requestNoContent(t, server.Client(), http.MethodDelete, server.URL+"/api/v2/sessions/"+session.ID)
	requestJSON[map[string]string](t, server.Client(), http.MethodGet,
		server.URL+"/api/v2/targets/"+targetID, nil, http.StatusNotFound)
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
	return httptest.NewServer(api.New(api.Config{
		Store: database, Artifacts: artifacts, Plugins: catalog, Runner: taskRunner,
	})), database, taskRunner, cancel
}

func assertReport(t *testing.T, report model.TargetReport) {
	t.Helper()
	if len(report.Tasks) != 1 || report.Tasks[0].Status != model.TaskSucceeded || report.Tasks[0].Inputs["request_label"] != "API run" {
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

func requestNoContent(t *testing.T, client *http.Client, method, url string) {
	t.Helper()
	request, err := http.NewRequest(method, url, nil)
	if err != nil {
		t.Fatal(err)
	}
	response, err := client.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusNoContent {
		body, _ := io.ReadAll(response.Body)
		t.Fatalf("%s %s status=%d, want %d: %s", method, url, response.StatusCode, http.StatusNoContent, body)
	}
}
