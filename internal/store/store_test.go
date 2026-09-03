package store

import (
	"context"
	"database/sql"
	"path/filepath"
	"testing"

	"github.com/owtf/owtf/internal/model"
	"github.com/owtf/owtf/internal/target"
)

func TestOpenMigratesPluginVariantToGroupAndType(t *testing.T) {
	path := filepath.Join(t.TempDir(), "owtf.db")
	legacy, err := sql.Open("sqlite3", path)
	if err != nil {
		t.Fatal(err)
	}
	_, err = legacy.Exec(`
CREATE TABLE plugins (
  id TEXT PRIMARY KEY, version TEXT NOT NULL, title TEXT NOT NULL,
  description TEXT NOT NULL, variant TEXT NOT NULL, techniques_json TEXT NOT NULL,
  runtime_type TEXT NOT NULL, availability TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL
);
INSERT INTO plugins VALUES('OWTF-TEST-001-passive','0.1.0','test','','passive','["OWTF-TEST-001"]','builtin','ready','','2026-01-01T00:00:00Z');`)
	if err != nil {
		legacy.Close()
		t.Fatal(err)
	}
	if err := legacy.Close(); err != nil {
		t.Fatal(err)
	}

	database, err := Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()
	plugins, err := database.ListPlugins(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(plugins) != 1 || plugins[0].Group != "web" || plugins[0].Type != "passive" {
		t.Fatalf("legacy plugin columns were not migrated: %+v", plugins)
	}
}

func TestReplacePluginsRemovesStaleCatalogEntries(t *testing.T) {
	database, err := Open(filepath.Join(t.TempDir(), "owtf.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()

	first := plugin("OWTF-TEST-001-active")
	second := plugin("OWTF-TEST-002-passive")
	if err := database.ReplacePlugins(context.Background(), []model.Plugin{first, second}); err != nil {
		t.Fatal(err)
	}
	if err := database.ReplacePlugins(context.Background(), []model.Plugin{second}); err != nil {
		t.Fatal(err)
	}
	plugins, err := database.ListPlugins(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(plugins) != 1 || plugins[0].ID != second.ID {
		t.Fatalf("stale plugins remain after catalog replacement: %+v", plugins)
	}
}

func TestDeleteTargetPrunesEmptyRun(t *testing.T) {
	database, err := Open(filepath.Join(t.TempDir(), "owtf.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()
	ctx := context.Background()
	session, err := database.CreateSession(ctx, "Cleanup")
	if err != nil {
		t.Fatal(err)
	}
	normalized, _ := target.Normalize("https://example.test")
	added, err := database.AddTargets(ctx, session.ID, []target.Normalized{normalized})
	if err != nil {
		t.Fatal(err)
	}
	if _, _, err := database.CreateRun(ctx, session.ID, []TaskSpec{{
		TargetID: added.Created[0].ID, PluginID: "OWTF-TEST-001-active", PluginVersion: "0.1.0", PluginSnapshot: "{}",
	}}); err != nil {
		t.Fatal(err)
	}
	if err := database.DeleteTarget(ctx, added.Created[0].ID); err != nil {
		t.Fatal(err)
	}
	var count int
	if err := database.db.QueryRowContext(ctx, `SELECT COUNT(*) FROM runs`).Scan(&count); err != nil {
		t.Fatal(err)
	}
	if count != 0 {
		t.Fatalf("empty run survived target deletion: %d", count)
	}
}

func TestBlockedPluginRemainsVisibleInWorklistAndRun(t *testing.T) {
	database, err := Open(filepath.Join(t.TempDir(), "owtf.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()
	ctx := context.Background()
	session, err := database.CreateSession(ctx, "Plugin group")
	if err != nil {
		t.Fatal(err)
	}
	normalized, _ := target.Normalize("https://example.test")
	added, err := database.AddTargets(ctx, session.ID, []target.Normalized{normalized})
	if err != nil {
		t.Fatal(err)
	}
	run, tasks, err := database.CreateRun(ctx, session.ID, []TaskSpec{
		{TargetID: added.Created[0].ID, PluginID: "OWTF-TEST-001-active", PluginVersion: "0.1.0", PluginSnapshot: "{}"},
		{TargetID: added.Created[0].ID, PluginID: "OWTF-TEST-002-active", PluginVersion: "0.1.0", PluginSnapshot: "{}", Status: model.TaskBlocked, Error: "missing commands: scanner"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if run.Status != model.RunQueued || len(tasks) != 2 || tasks[1].Status != model.TaskBlocked || tasks[1].EndedAt == nil {
		t.Fatalf("unexpected initial run: run=%+v tasks=%+v", run, tasks)
	}
	events, err := database.ListTaskEvents(ctx, tasks[1].ID)
	if err != nil || len(events) != 1 || events[0].Message != "task blocked: missing commands: scanner" {
		t.Fatalf("blocked task event is missing: events=%+v err=%v", events, err)
	}
	execution, err := database.StartTask(ctx, tasks[0].ID)
	if err != nil {
		t.Fatal(err)
	}
	if err := database.CompleteTask(ctx, execution, nil, nil, nil, nil); err != nil {
		t.Fatal(err)
	}
	finished, err := database.GetRun(ctx, run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if finished.Status != model.RunBlocked || finished.FinishedAt == nil {
		t.Fatalf("run did not retain blocked status: %+v", finished)
	}
}

func plugin(id string) model.Plugin {
	return model.Plugin{
		ID: id, Version: "0.1.0", Title: id, Group: "web", Type: "active",
		Techniques: []string{id}, RuntimeType: "builtin", Availability: "ready",
	}
}
