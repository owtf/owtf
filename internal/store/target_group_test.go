package store

import (
	"context"
	"github.com/owtf/owtf/internal/target"
	"path/filepath"
	"testing"
)

func TestTargetGroupPreservesURLIdentityAndSessionBoundary(t *testing.T) {
	db, err := Open(filepath.Join(t.TempDir(), "test.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	ctx := context.Background()
	session, err := db.CreateSession(ctx, "one")
	if err != nil {
		t.Fatal(err)
	}
	var seeds []target.Normalized
	for _, value := range []string{"https://example.test/a", "http://example.test:8080/b", "https://other.example.test/a"} {
		seed, err := target.Normalize(value)
		if err != nil {
			t.Fatal(err)
		}
		seeds = append(seeds, seed)
	}
	added, err := db.AddTargets(ctx, session.ID, seeds)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := db.UpdateTargetScope(ctx, added.Created[1].ID, false); err != nil {
		t.Fatal(err)
	}
	other, err := db.CreateSession(ctx, "two")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := db.AddTargets(ctx, other.ID, seeds); err != nil {
		t.Fatal(err)
	}
	report, err := db.GetTargetGroupReport(ctx, added.Created[0].ID)
	if err != nil {
		t.Fatal(err)
	}
	if report.Host != "example.test" || len(report.Targets) != 2 {
		t.Fatalf("group = %+v", report.Targets)
	}
	for _, member := range report.Targets {
		if member.SessionID != session.ID {
			t.Fatal("cross-session target")
		}
		if member.ID == added.Created[1].ID && member.Scope {
			t.Fatal("scope broadened")
		}
	}
	original, err := db.GetTarget(ctx, added.Created[0].ID)
	if err != nil || original.Value != seeds[0].Value {
		t.Fatalf("identity changed: %+v %v", original, err)
	}
}
