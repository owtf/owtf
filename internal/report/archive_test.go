package report

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"io"
	"strings"
	"testing"
	"time"

	"github.com/owtf/owtf/internal/artifact"
	"github.com/owtf/owtf/internal/model"
)

func TestWriteSessionArchiveIncludesPortableEvidence(t *testing.T) {
	artifacts, err := artifact.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	stored, err := artifacts.Put([]byte("captured evidence"))
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now().UTC().Truncate(time.Second)
	session := model.SessionReport{
		Session: model.Session{ID: "ses_1", Name: "Escaping <script>alert(1)</script>", CreatedAt: now},
		Summary: model.ReportSummary{Targets: 1, Runs: 1, Tasks: 1, Attempts: 1, Succeeded: 1, Artifacts: 1},
		Targets: []model.Target{{ID: "tgt_1", SessionID: "ses_1", Kind: "url", Value: "https://example.test/?q=<script>", CreatedAt: now}},
		Tasks:   []model.Task{{ID: "tsk_1", RunID: "run_1", TargetID: "tgt_1", PluginID: "OWTF-WSP-001-active", Status: model.TaskSucceeded, CreatedAt: now}},
		Attempts: []model.TaskAttempt{{
			ID: "att_1", TaskID: "tsk_1", AttemptNumber: 1, Status: model.TaskSucceeded, StartedAt: now, EndedAt: &now,
		}},
		Artifacts: []model.Artifact{{
			ID: "art_1", TaskID: "tsk_1", Name: `..\..\evidence.txt`, MediaType: "text/plain",
			Size: stored.Size, SHA256: stored.SHA256, Path: stored.Path, CreatedAt: now,
		}},
	}

	var output bytes.Buffer
	if err := WriteSessionArchive(&output, session, artifacts); err != nil {
		t.Fatal(err)
	}
	reader, err := zip.NewReader(bytes.NewReader(output.Bytes()), int64(output.Len()))
	if err != nil {
		t.Fatal(err)
	}
	files := make(map[string][]byte, len(reader.File))
	for _, item := range reader.File {
		file, err := item.Open()
		if err != nil {
			t.Fatal(err)
		}
		files[item.Name], err = io.ReadAll(file)
		file.Close()
		if err != nil {
			t.Fatal(err)
		}
	}
	for _, name := range []string{"report.json", "manifest.json", "index.html", "artifacts/art_1/evidence.txt"} {
		if _, ok := files[name]; !ok {
			t.Errorf("archive is missing %s", name)
		}
	}
	if string(files["artifacts/art_1/evidence.txt"]) != "captured evidence" {
		t.Fatalf("unexpected artifact bytes: %q", files["artifacts/art_1/evidence.txt"])
	}
	if strings.Contains(string(files["index.html"]), "<script>alert(1)</script>") ||
		!strings.Contains(string(files["index.html"]), "&lt;script&gt;") {
		t.Fatal("offline report did not escape operator-controlled content")
	}
	var decoded model.SessionReport
	if err := json.Unmarshal(files["report.json"], &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded.Session.ID != session.Session.ID || len(decoded.Attempts) != 1 || len(decoded.Artifacts) != 1 {
		t.Fatalf("unexpected JSON report: %+v", decoded)
	}
	var metadata manifest
	if err := json.Unmarshal(files["manifest.json"], &metadata); err != nil {
		t.Fatal(err)
	}
	if metadata.Format != archiveFormat || metadata.ArtifactFiles["art_1"] != "artifacts/art_1/evidence.txt" {
		t.Fatalf("unexpected manifest: %+v", metadata)
	}
}
