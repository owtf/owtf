package main

import (
	"context"
	"github.com/owtf/owtf/internal/har"
	"github.com/owtf/owtf/internal/store"
	"github.com/owtf/owtf/internal/target"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestProxyAttachmentPersistsOnlySelectedOrigin(t *testing.T) {
	dir := t.TempDir()
	attachment, closeAttachment, err := openProxyAttachment(dir)
	if err != nil {
		t.Fatal(err)
	}
	defer closeAttachment()
	db, err := store.Open(filepath.Join(dir, "owtf.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	ctx := context.Background()
	session, err := db.CreateSession(ctx, "capture")
	if err != nil {
		t.Fatal(err)
	}
	seed, err := target.Normalize("http://example.test:8080/")
	if err != nil {
		t.Fatal(err)
	}
	added, err := db.AddTargets(ctx, session.ID, []target.Normalized{seed})
	if err != nil {
		t.Fatal(err)
	}
	id := added.Created[0].ID
	req := httptest.NewRequest(http.MethodPut, "/capture", strings.NewReader(`{"target_id":"`+id+`"}`))
	req.Header.Set("Content-Type", "application/json")
	response := httptest.NewRecorder()
	attachment.ServeHTTP(response, req)
	if response.Code != 200 {
		t.Fatal(response.Body.String())
	}
	save := attachment.Snapshot()
	item := har.Transaction{Method: "GET", URL: "http://example.test:8080/account", RequestHeaders: "{}", ResponseHeaders: "{}", StatusCode: 200, ResponseBody: []byte("actual body"), ResponseMediaType: "text/plain", StartedAt: time.Now().UTC()}
	if err := save(item); err != nil {
		t.Fatal(err)
	}
	item.URL = "http://example.test:9090/account"
	if err := save(item); err != nil {
		t.Fatal(err)
	}
	report, err := db.GetTargetReport(ctx, id)
	if err != nil {
		t.Fatal(err)
	}
	if len(report.Transactions) != 1 || len(report.Artifacts) != 1 {
		t.Fatalf("transactions=%d artifacts=%d", len(report.Transactions), len(report.Artifacts))
	}
	if _, err := db.UpdateTargetScope(ctx, id, false); err != nil {
		t.Fatal(err)
	}
	if err := save(item); err == nil {
		t.Fatal("saved to out-of-scope target")
	}
}
