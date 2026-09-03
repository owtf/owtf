package store

import (
	"context"
	"database/sql"
	"path/filepath"
	"testing"
	"time"

	"github.com/owtf/owtf/internal/model"
	"github.com/owtf/owtf/internal/target"
)

func TestOpenMigratesTaskOwnedTransactions(t *testing.T) {
	path := filepath.Join(t.TempDir(), "owtf.db")
	legacy, err := sql.Open("sqlite3", path)
	if err != nil {
		t.Fatal(err)
	}
	_, err = legacy.Exec(`
CREATE TABLE sessions (id INTEGER PRIMARY KEY, public_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE targets (id INTEGER PRIMARY KEY, public_id TEXT NOT NULL UNIQUE, session_id INTEGER NOT NULL, kind TEXT NOT NULL, original TEXT NOT NULL, value TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(session_id, value));
CREATE TABLE runs (id INTEGER PRIMARY KEY, public_id TEXT NOT NULL UNIQUE, session_id INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT);
CREATE TABLE tasks (id INTEGER PRIMARY KEY, public_id TEXT NOT NULL UNIQUE, run_id INTEGER NOT NULL, target_id INTEGER NOT NULL, plugin_id TEXT NOT NULL, plugin_version TEXT NOT NULL, plugin_snapshot TEXT NOT NULL, status TEXT NOT NULL, error TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, started_at TEXT, ended_at TEXT);
CREATE TABLE artifacts (id INTEGER PRIMARY KEY, public_id TEXT NOT NULL UNIQUE, task_id INTEGER NOT NULL, name TEXT NOT NULL, media_type TEXT NOT NULL, size INTEGER NOT NULL, sha256 TEXT NOT NULL, path TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE http_exchanges (id INTEGER PRIMARY KEY, public_id TEXT NOT NULL UNIQUE, task_id INTEGER NOT NULL, target_id INTEGER NOT NULL, method TEXT NOT NULL, url TEXT NOT NULL, request_headers TEXT NOT NULL, status_code INTEGER NOT NULL, response_headers TEXT NOT NULL, response_body_artifact_id INTEGER, duration_ms INTEGER NOT NULL, created_at TEXT NOT NULL);
INSERT INTO sessions VALUES(1, 'ses_old', 'Old session', '2026-01-01T00:00:00Z');
INSERT INTO targets VALUES(1, 'tgt_old', 1, 'url', 'https://example.test', 'https://example.test/', '2026-01-01T00:00:00Z');
INSERT INTO runs VALUES(1, 'run_old', 1, 'succeeded', '2026-01-01T00:00:00Z', NULL, NULL);
INSERT INTO tasks VALUES(1, 'tsk_old', 1, 1, 'OWTF-TEST-001-active', '0.1.0', '{}', 'succeeded', '', '2026-01-01T00:00:00Z', NULL, NULL);
INSERT INTO artifacts VALUES(1, 'art_old', 1, 'body', 'text/plain', 4, 'hash', 'aa/hash', '2026-01-01T00:00:00Z');
INSERT INTO http_exchanges VALUES(1, 'txn_old', 1, 1, 'GET', 'https://example.test/', '{}', 200, '{}', 1, 5, '2026-01-01T00:00:00Z');`)
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
	transactions, err := database.ListTransactions(context.Background(), "ses_old", "tgt_old")
	if err != nil {
		t.Fatal(err)
	}
	if len(transactions) != 1 || transactions[0].ID != "txn_old" || transactions[0].TaskID != "tsk_old" || transactions[0].ResponseBodyArtifactID != "art_old" {
		t.Fatalf("transaction was not migrated: %+v", transactions)
	}
	run, err := database.GetRun(context.Background(), "run_old")
	if err != nil || run.Profile != "" {
		t.Fatalf("run profile was not migrated: run=%+v err=%v", run, err)
	}
	artifact, err := database.GetArtifact(context.Background(), "art_old")
	if err != nil || artifact.TargetID != "tgt_old" || artifact.TaskID != "tsk_old" {
		t.Fatalf("artifact was not migrated: artifact=%+v err=%v", artifact, err)
	}
	columns, err := database.tableColumns(context.Background(), "transactions")
	if err != nil || !columns["source_artifact_id"] || !columns["request_body_artifact_id"] {
		t.Fatalf("transaction columns are incomplete: columns=%v err=%v", columns, err)
	}
}

func TestImportAndDeleteTargetTransactions(t *testing.T) {
	database, err := Open(filepath.Join(t.TempDir(), "owtf.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()
	ctx := context.Background()
	session, _ := database.CreateSession(ctx, "Import")
	normalized, _ := target.Normalize("https://example.test")
	added, _ := database.AddTargets(ctx, session.ID, []target.Normalized{normalized})
	targetID := added.Created[0].ID
	now := time.Now().UTC()
	artifacts := []model.Artifact{
		{ID: "art_source", TargetID: targetID, Name: "capture.har", MediaType: "application/json", Size: 10, SHA256: "source", Path: "aa/source", CreatedAt: now},
		{ID: "art_request", TargetID: targetID, Name: "request", MediaType: "text/plain", Size: 7, SHA256: "request", Path: "aa/request", CreatedAt: now},
		{ID: "art_response", TargetID: targetID, Name: "response", MediaType: "text/plain", Size: 8, SHA256: "response", Path: "aa/response", CreatedAt: now},
	}
	transaction := model.Transaction{
		ID: "txn_import", TargetID: targetID, Method: "POST", URL: "https://example.test/submit",
		RequestHeaders: "{}", StatusCode: 201, ResponseHeaders: "{}", SourceArtifactID: "art_source",
		RequestBodyArtifactID: "art_request", ResponseBodyArtifactID: "art_response", DurationMS: 12, CreatedAt: now,
	}
	invalid := transaction
	invalid.ID = "txn_invalid"
	invalid.ResponseBodyArtifactID = "art_missing"
	if err := database.ImportTransactions(ctx, targetID, artifacts, []model.Transaction{invalid}); err == nil {
		t.Fatal("import accepted an unknown artifact")
	}
	report, err := database.GetTargetReport(ctx, targetID)
	if err != nil || len(report.Artifacts) != 0 || len(report.Transactions) != 0 {
		t.Fatalf("failed import was not atomic: report=%+v err=%v", report, err)
	}
	if err := database.ImportTransactions(ctx, targetID, artifacts, []model.Transaction{transaction}); err != nil {
		t.Fatal(err)
	}
	stored, err := database.GetTransaction(ctx, targetID, transaction.ID)
	if err != nil || stored.TaskID != "" || stored.SourceArtifactID != "art_source" || stored.RequestBodyArtifactID != "art_request" {
		t.Fatalf("unexpected imported transaction: transaction=%+v err=%v", stored, err)
	}
	if tasks, _ := database.ListTasks(ctx, session.ID, ""); len(tasks) != 0 {
		t.Fatalf("transaction import created worklist tasks: %+v", tasks)
	}
	if err := database.DeleteTransaction(ctx, targetID, transaction.ID); err != nil {
		t.Fatal(err)
	}
	report, err = database.GetTargetReport(ctx, targetID)
	if err != nil || len(report.Artifacts) != 0 || len(report.Transactions) != 0 {
		t.Fatalf("transaction deletion left imported records: report=%+v err=%v", report, err)
	}
}

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
	if _, _, err := database.CreateRun(ctx, session.ID, "", []TaskSpec{{
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
	run, tasks, err := database.CreateRun(ctx, session.ID, "default", []TaskSpec{
		{TargetID: added.Created[0].ID, PluginID: "OWTF-TEST-001-active", PluginVersion: "0.1.0", PluginSnapshot: "{}"},
		{TargetID: added.Created[0].ID, PluginID: "OWTF-TEST-002-active", PluginVersion: "0.1.0", PluginSnapshot: "{}", Status: model.TaskBlocked, Error: "missing commands: scanner"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if run.Profile != "default" || run.Status != model.RunQueued || len(tasks) != 2 || tasks[1].Status != model.TaskBlocked || tasks[1].EndedAt == nil {
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
	if finished.Profile != "default" || finished.Status != model.RunBlocked || finished.FinishedAt == nil {
		t.Fatalf("run did not retain blocked status: %+v", finished)
	}
}

func plugin(id string) model.Plugin {
	return model.Plugin{
		ID: id, Version: "0.1.0", Title: id, Group: "web", Type: "active",
		Techniques: []string{id}, RuntimeType: "builtin", Availability: "ready",
	}
}
