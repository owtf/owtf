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
	externalData, err := json.Marshal(model.ExternalOutput{
		Guidance: "Review <response> markers.",
		References: []model.ExternalReference{
			{Title: "OWASP guide", URL: "https://owasp.org/guide"},
			{Title: "Unsafe <link>", URL: "javascript:alert(1)"},
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	grepData, err := json.Marshal(model.GrepOutput{
		RuleID: "server-header", Title: "Server header", Source: "response_headers",
		TransactionIDs: []string{"txn_1"},
	})
	if err != nil {
		t.Fatal(err)
	}
	session := model.SessionReport{
		Session: model.Session{ID: "ses_1", Name: "Escaping <script>alert(1)</script>", CreatedAt: now},
		Summary: model.ReportSummary{Targets: 1, Runs: 1, Tasks: 1, Attempts: 1, Succeeded: 1, Transactions: 1, Artifacts: 1, Observations: 2},
		Targets: []model.Target{{ID: "tgt_1", SessionID: "ses_1", Kind: "url", Value: "https://example.test/?q=<script>", CreatedAt: now}},
		Tasks: []model.Task{{
			ID: "tsk_1", RunID: "run_1", TargetID: "tgt_1", PluginID: "OWTF-WSP-001-active",
			Techniques: []model.Technique{{Code: "OWTF-WSP-001", Title: "Visit URLs", Hint: "Visit the target.", Priority: 99, Reference: "https://owtf.org"}},
			Status:     model.TaskSucceeded, CreatedAt: now,
		}},
		PluginOutputReviews: []model.PluginOutputReview{{
			TaskID: "tsk_1", Rank: model.PluginOutputRankHigh, Notes: "Verified manually <script>alert(2)</script>", UpdatedAt: &now,
		}},
		Attempts: []model.TaskAttempt{{
			ID: "att_1", TaskID: "tsk_1", AttemptNumber: 1, Status: model.TaskSucceeded, StartedAt: now, EndedAt: &now,
		}},
		Observations: []model.Observation{{
			ID: "obs_1", TaskID: "tsk_1", TargetID: "tgt_1", TechniqueCode: "OWTF-WSP-001",
			Kind: model.ObservationKindExternalReferences, Data: string(externalData), CreatedAt: now,
		}, {
			ID: "obs_2", TaskID: "tsk_1", TargetID: "tgt_1", TechniqueCode: "OWTF-WSP-001",
			Kind: model.ObservationKindGrepMatches, Data: string(grepData), CreatedAt: now,
		}},
		Transactions: []model.Transaction{{
			ID: "txn_1", TargetID: "tgt_1", Method: "GET", URL: "https://example.test/", StatusCode: 200, CreatedAt: now,
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
	if !strings.Contains(string(files["index.html"]), "OWTF-WSP-001") ||
		!strings.Contains(string(files["index.html"]), "Visit URLs") ||
		!strings.Contains(string(files["index.html"]), "https://owtf.org") {
		t.Fatal("offline report omitted technique metadata")
	}
	if !strings.Contains(string(files["index.html"]), "Review &lt;response&gt; markers.") ||
		!strings.Contains(string(files["index.html"]), "https://owasp.org/guide") ||
		!strings.Contains(string(files["index.html"]), "#ZgotmplZ") {
		t.Fatal("offline report omitted or unsafely rendered external guidance")
	}
	if !strings.Contains(string(files["index.html"]), `href="#transaction-txn_1"`) ||
		!strings.Contains(string(files["index.html"]), `id="transaction-txn_1"`) {
		t.Fatal("offline report did not link grep output to its transaction")
	}
	if !strings.Contains(string(files["index.html"]), model.PluginOutputRankHigh) ||
		!strings.Contains(string(files["index.html"]), "Verified manually &lt;script&gt;alert(2)&lt;/script&gt;") ||
		strings.Contains(string(files["index.html"]), "Verified manually <script>") {
		t.Fatal("offline report omitted or unsafely rendered plugin output review")
	}
	var decoded model.SessionReport
	if err := json.Unmarshal(files["report.json"], &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded.Session.ID != session.Session.ID || len(decoded.Attempts) != 1 || len(decoded.PluginOutputReviews) != 1 || len(decoded.Artifacts) != 1 || len(decoded.Observations) != 2 || len(decoded.Transactions) != 1 {
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
