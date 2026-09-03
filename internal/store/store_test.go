package store

import (
	"context"
	"path/filepath"
	"testing"

	"github.com/owtf/owtf/internal/model"
	"github.com/owtf/owtf/internal/target"
)

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

func plugin(id string) model.Plugin {
	return model.Plugin{
		ID: id, Version: "0.1.0", Title: id, Variant: "active",
		Techniques: []string{id}, RuntimeType: "builtin", Availability: "ready",
	}
}
