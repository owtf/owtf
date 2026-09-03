package runner_test

import (
	"context"
	"encoding/json"
	"path/filepath"
	"testing"
	"testing/fstest"
	"time"

	"github.com/owtf/owtf/internal/artifact"
	"github.com/owtf/owtf/internal/model"
	"github.com/owtf/owtf/internal/plugin"
	"github.com/owtf/owtf/internal/runner"
	"github.com/owtf/owtf/internal/store"
	"github.com/owtf/owtf/internal/target"
)

const blockingManifest = `apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-TEST-001-active
  version: 0.1.0
  title: Blocking test plugin
spec:
  techniques: [OWTF-TEST-001]
  group: web
  type: active
  runtime:
    type: builtin
    builtin: blocking
`

const grepManifest = `apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-TEST-002-grep
  version: 0.1.0
  title: Transaction grep
spec:
  techniques: [OWTF-TEST-002]
  group: web
  type: grep
  targetKinds: [url]
  runtime:
    type: grep
    grep:
      rules:
        - id: server-header
          title: Server header
          source: response_headers
          pattern: (?i)server
        - id: generator-meta
          title: Generator metadata
          source: response_body
          pattern: (?i)generator
`

func TestCancelStopsTaskAndReleasesWorker(t *testing.T) {
	database, err := store.Open(filepath.Join(t.TempDir(), "owtf.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()
	artifacts, err := artifact.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	catalog, err := plugin.Load(fstest.MapFS{"plugin.yaml": &fstest.MapFile{Data: []byte(blockingManifest)}})
	if err != nil {
		t.Fatal(err)
	}
	started := make(chan struct{}, 1)
	catalog.RegisterBuiltin("blocking", func(ctx context.Context, _ plugin.Request) (plugin.Result, error) {
		started <- struct{}{}
		<-ctx.Done()
		return plugin.Result{}, ctx.Err()
	})
	entry, _ := catalog.Get("OWTF-TEST-001-active")
	if err := database.ReplacePlugins(context.Background(), []model.Plugin{entry.Plugin()}); err != nil {
		t.Fatal(err)
	}
	session, err := database.CreateSession(context.Background(), "Cancellation")
	if err != nil {
		t.Fatal(err)
	}
	normalized, _ := target.Normalize("https://example.test")
	added, err := database.AddTargets(context.Background(), session.ID, []target.Normalized{normalized})
	if err != nil {
		t.Fatal(err)
	}
	snapshot, _ := entry.Snapshot(nil)
	_, tasks, err := database.CreateRun(context.Background(), session.ID, "", []store.TaskSpec{{
		TargetID: added.Created[0].ID, PluginID: entry.Manifest.Metadata.ID,
		PluginVersion: entry.Manifest.Metadata.Version, PluginSnapshot: snapshot,
	}})
	if err != nil {
		t.Fatal(err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	taskRunner := runner.New(database, artifacts, catalog, 1, time.Minute)
	if err := taskRunner.Start(ctx); err != nil {
		t.Fatal(err)
	}
	defer taskRunner.Stop()
	if err := taskRunner.Submit([]string{tasks[0].ID}); err != nil {
		t.Fatal(err)
	}
	select {
	case <-started:
	case <-time.After(time.Second):
		t.Fatal("plugin did not start")
	}
	workers := taskRunner.Workers()
	if len(workers) != 1 || workers[0].Status != "running" || workers[0].TaskID != tasks[0].ID {
		t.Fatalf("unexpected running worker: %+v", workers)
	}
	if _, err := taskRunner.Cancel(context.Background(), tasks[0].ID); err != nil {
		t.Fatal(err)
	}

	want(t, time.Second, func() bool {
		task, err := database.GetTask(context.Background(), tasks[0].ID)
		return err == nil && task.Status == model.TaskCancelled
	}, "task did not become cancelled")
	want(t, time.Second, func() bool {
		worker := taskRunner.Workers()[0]
		return worker.Status == "idle" && worker.Cancelled == 1 && worker.TaskID == ""
	}, "worker did not return to idle")
	events, err := database.ListTaskEvents(context.Background(), tasks[0].ID)
	if err != nil {
		t.Fatal(err)
	}
	if len(events) < 2 || events[len(events)-1].Message != "task cancelled" {
		t.Fatalf("cancellation event missing: %+v", events)
	}
	attempts, err := database.ListTaskAttempts(context.Background(), tasks[0].ID)
	if err != nil || len(attempts) != 1 || attempts[0].Status != model.TaskCancelled {
		t.Fatalf("unexpected cancellation attempts: attempts=%+v err=%v", attempts, err)
	}
	worker := taskRunner.Workers()[0]
	if worker.Status != "idle" || worker.Cancelled != 1 || worker.Completed != 0 {
		t.Fatalf("unexpected worker state after cancellation: %+v", worker)
	}
}

func TestGrepPluginReadsCapturedTransactionEvidence(t *testing.T) {
	database, err := store.Open(filepath.Join(t.TempDir(), "owtf.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()
	artifacts, err := artifact.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	catalog, err := plugin.Load(fstest.MapFS{"plugin.yaml": {Data: []byte(grepManifest)}})
	if err != nil {
		t.Fatal(err)
	}
	entry, _ := catalog.Get("OWTF-TEST-002-grep")
	if err := database.ReplacePlugins(context.Background(), []model.Plugin{entry.Plugin()}); err != nil {
		t.Fatal(err)
	}

	session, err := database.CreateSession(context.Background(), "Grep")
	if err != nil {
		t.Fatal(err)
	}
	normalized, _ := target.Normalize("https://example.test")
	added, err := database.AddTargets(context.Background(), session.ID, []target.Normalized{normalized})
	if err != nil {
		t.Fatal(err)
	}
	targetID := added.Created[0].ID
	body, err := artifacts.Put([]byte(`<meta name="generator" content="OWTF">`))
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now().UTC()
	bodyArtifact := model.Artifact{
		ID: "art_body", TargetID: targetID, Name: "response-body", MediaType: "text/html",
		Size: body.Size, SHA256: body.SHA256, Path: body.Path, CreatedAt: now,
	}
	transaction := model.Transaction{
		ID: "txn_captured", TargetID: targetID, Method: "GET", URL: normalized.Value,
		ResponseHeaders: `{"Server":["Caddy"]}`, ResponseBodyArtifactID: bodyArtifact.ID,
		StatusCode: 200, CreatedAt: now,
	}
	if err := database.ImportTransactions(context.Background(), targetID, []model.Artifact{bodyArtifact}, []model.Transaction{transaction}); err != nil {
		t.Fatal(err)
	}
	snapshot, err := entry.Snapshot(nil)
	if err != nil {
		t.Fatal(err)
	}
	_, tasks, err := database.CreateRun(context.Background(), session.ID, "", []store.TaskSpec{{
		TargetID: targetID, PluginID: entry.Manifest.Metadata.ID, PluginVersion: entry.Manifest.Metadata.Version,
		PluginSnapshot: snapshot, Status: model.TaskQueued,
	}})
	if err != nil {
		t.Fatal(err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	taskRunner := runner.New(database, artifacts, catalog, 1, time.Minute)
	if err := taskRunner.Start(ctx); err != nil {
		t.Fatal(err)
	}
	defer taskRunner.Stop()
	if err := taskRunner.Submit([]string{tasks[0].ID}); err != nil {
		t.Fatal(err)
	}
	want(t, time.Second, func() bool {
		task, err := database.GetTask(context.Background(), tasks[0].ID)
		return err == nil && task.Status == model.TaskSucceeded
	}, "grep task did not succeed")

	report, err := database.GetTargetReport(context.Background(), targetID)
	if err != nil {
		t.Fatal(err)
	}
	if len(report.Transactions) != 1 || len(report.Observations) != 2 {
		t.Fatalf("grep changed evidence or omitted output: %+v", report)
	}
	for _, observation := range report.Observations {
		if observation.Kind != model.ObservationKindGrepMatches {
			t.Fatalf("unexpected grep observation kind: %+v", observation)
		}
		var output model.GrepOutput
		if err := json.Unmarshal([]byte(observation.Data), &output); err != nil {
			t.Fatalf("decode grep observation: %v", err)
		}
		if len(output.TransactionIDs) != 1 || output.TransactionIDs[0] != transaction.ID {
			t.Fatalf("unexpected grep observation: %+v", observation)
		}
	}
}

func TestPauseResumeAndReorderChangeDispatchOrder(t *testing.T) {
	database, err := store.Open(filepath.Join(t.TempDir(), "owtf.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()
	artifacts, err := artifact.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	catalog, err := plugin.Load(fstest.MapFS{"plugin.yaml": {Data: []byte(blockingManifest)}})
	if err != nil {
		t.Fatal(err)
	}
	started := make(chan string, 3)
	catalog.RegisterBuiltin("blocking", func(ctx context.Context, request plugin.Request) (plugin.Result, error) {
		started <- request.TaskID
		<-ctx.Done()
		return plugin.Result{}, ctx.Err()
	})
	entry, _ := catalog.Get("OWTF-TEST-001-active")
	if err := database.ReplacePlugins(context.Background(), []model.Plugin{entry.Plugin()}); err != nil {
		t.Fatal(err)
	}
	session, _ := database.CreateSession(context.Background(), "Worklist")
	normalized, _ := target.Normalize("https://example.test")
	added, _ := database.AddTargets(context.Background(), session.ID, []target.Normalized{normalized})

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	taskRunner := runner.New(database, artifacts, catalog, 1, time.Minute)
	if err := taskRunner.Start(ctx); err != nil {
		t.Fatal(err)
	}
	defer taskRunner.Stop()
	snapshot, _ := entry.Snapshot(nil)
	_, tasks, err := database.CreateRun(context.Background(), session.ID, "", []store.TaskSpec{
		{TargetID: added.Created[0].ID, PluginID: entry.Manifest.Metadata.ID, PluginVersion: entry.Manifest.Metadata.Version, PluginSnapshot: snapshot},
		{TargetID: added.Created[0].ID, PluginID: entry.Manifest.Metadata.ID, PluginVersion: entry.Manifest.Metadata.Version, PluginSnapshot: snapshot},
		{TargetID: added.Created[0].ID, PluginID: entry.Manifest.Metadata.ID, PluginVersion: entry.Manifest.Metadata.Version, PluginSnapshot: snapshot},
	})
	if err != nil {
		t.Fatal(err)
	}
	if err := taskRunner.Submit([]string{tasks[0].ID, tasks[1].ID, tasks[2].ID}); err != nil {
		t.Fatal(err)
	}
	next := func() string {
		t.Helper()
		select {
		case id := <-started:
			return id
		case <-time.After(time.Second):
			t.Fatal("plugin did not start")
			return ""
		}
	}
	if id := next(); id != tasks[0].ID {
		t.Fatalf("first task = %s, want %s", id, tasks[0].ID)
	}
	if _, err := taskRunner.Pause(context.Background(), tasks[1].ID); err != nil {
		t.Fatal(err)
	}
	if _, err := taskRunner.Reorder(context.Background(), session.ID, []string{tasks[1].ID, tasks[2].ID}); err != nil {
		t.Fatal(err)
	}
	if _, err := taskRunner.Resume(context.Background(), tasks[1].ID); err != nil {
		t.Fatal(err)
	}
	if _, err := taskRunner.Cancel(context.Background(), tasks[0].ID); err != nil {
		t.Fatal(err)
	}
	if id := next(); id != tasks[1].ID {
		t.Fatalf("reordered task = %s, want %s", id, tasks[1].ID)
	}
	if _, err := taskRunner.Cancel(context.Background(), tasks[1].ID); err != nil {
		t.Fatal(err)
	}
	if id := next(); id != tasks[2].ID {
		t.Fatalf("last task = %s, want %s", id, tasks[2].ID)
	}
	if _, err := taskRunner.Cancel(context.Background(), tasks[2].ID); err != nil {
		t.Fatal(err)
	}
}

func want(t *testing.T, timeout time.Duration, condition func() bool, message string) {
	t.Helper()
	deadline := time.Now().Add(timeout)
	for !condition() {
		if time.Now().After(deadline) {
			t.Fatal(message)
		}
		time.Sleep(10 * time.Millisecond)
	}
}
