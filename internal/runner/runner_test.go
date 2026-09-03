package runner_test

import (
	"context"
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
	snapshot, _ := entry.Snapshot()
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
	if err := taskRunner.Submit(ctx, []string{tasks[0].ID}); err != nil {
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
