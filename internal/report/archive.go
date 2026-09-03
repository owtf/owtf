package report

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"fmt"
	"html/template"
	"io"
	"path"
	"strings"
	"time"

	"github.com/owtf/owtf/internal/artifact"
	"github.com/owtf/owtf/internal/model"
)

const archiveFormat = "owtf-session-export/v1"

type manifest struct {
	Format        string            `json:"format"`
	ExportedAt    time.Time         `json:"exported_at"`
	SessionID     string            `json:"session_id"`
	ArtifactFiles map[string]string `json:"artifact_files"`
}

// WriteSessionArchive writes a portable ZIP containing the complete JSON
// report, an offline HTML summary, and every retained artifact.
func WriteSessionArchive(destination io.Writer, session model.SessionReport, artifacts *artifact.Store) error {
	artifactFiles := make(map[string]string, len(session.Artifacts))
	for _, item := range session.Artifacts {
		artifactFiles[item.ID] = archiveArtifactPath(item)
	}
	reviewByTask := make(map[string]model.PluginOutputReview, len(session.Tasks))
	for _, task := range session.Tasks {
		reviewByTask[task.ID] = model.PluginOutputReview{TaskID: task.ID, Rank: model.PluginOutputRankUnranked}
	}
	for _, review := range session.PluginOutputReviews {
		reviewByTask[review.TaskID] = review
	}

	reportJSON, err := json.MarshalIndent(session, "", "  ")
	if err != nil {
		return fmt.Errorf("encode report: %w", err)
	}
	manifestJSON, err := json.MarshalIndent(manifest{
		Format: archiveFormat, ExportedAt: time.Now().UTC(), SessionID: session.Session.ID,
		ArtifactFiles: artifactFiles,
	}, "", "  ")
	if err != nil {
		return fmt.Errorf("encode manifest: %w", err)
	}
	var reportHTML bytes.Buffer
	if err := sessionTemplate.Execute(&reportHTML, struct {
		Report        model.SessionReport
		ArtifactFiles map[string]string
		ReviewByTask  map[string]model.PluginOutputReview
	}{Report: session, ArtifactFiles: artifactFiles, ReviewByTask: reviewByTask}); err != nil {
		return fmt.Errorf("render report HTML: %w", err)
	}

	archive := zip.NewWriter(destination)
	if err := writeBytes(archive, "report.json", "application/json", reportJSON); err != nil {
		return err
	}
	if err := writeBytes(archive, "manifest.json", "application/json", manifestJSON); err != nil {
		return err
	}
	if err := writeBytes(archive, "index.html", "text/html; charset=utf-8", reportHTML.Bytes()); err != nil {
		return err
	}
	for _, item := range session.Artifacts {
		file, err := artifacts.Open(item.Path)
		if err != nil {
			return fmt.Errorf("open artifact %s: %w", item.ID, err)
		}
		header := &zip.FileHeader{Name: artifactFiles[item.ID], Method: zip.Deflate}
		header.SetModTime(item.CreatedAt)
		header.SetMode(0o640)
		header.Comment = item.MediaType
		entry, err := archive.CreateHeader(header)
		if err == nil {
			_, err = io.Copy(entry, file)
		}
		closeErr := file.Close()
		if err != nil {
			return fmt.Errorf("write artifact %s: %w", item.ID, err)
		}
		if closeErr != nil {
			return fmt.Errorf("close artifact %s: %w", item.ID, closeErr)
		}
	}
	if err := archive.Close(); err != nil {
		return fmt.Errorf("close report archive: %w", err)
	}
	return nil
}

func writeBytes(archive *zip.Writer, name, mediaType string, data []byte) error {
	header := &zip.FileHeader{Name: name, Method: zip.Deflate, Comment: mediaType}
	header.SetMode(0o640)
	entry, err := archive.CreateHeader(header)
	if err != nil {
		return fmt.Errorf("create %s: %w", name, err)
	}
	if _, err := entry.Write(data); err != nil {
		return fmt.Errorf("write %s: %w", name, err)
	}
	return nil
}

func archiveArtifactPath(item model.Artifact) string {
	name := path.Base(strings.ReplaceAll(item.Name, `\`, "/"))
	if name == "." || name == "/" || name == "" {
		name = "artifact"
	}
	return path.Join("artifacts", item.ID, name)
}

func externalOutput(observation model.Observation) *model.ExternalOutput {
	if observation.Kind != model.ObservationKindExternalReferences {
		return nil
	}
	var output model.ExternalOutput
	if err := json.Unmarshal([]byte(observation.Data), &output); err != nil {
		return nil
	}
	return &output
}

func grepOutput(observation model.Observation) *model.GrepOutput {
	if observation.Kind != model.ObservationKindGrepMatches {
		return nil
	}
	var output model.GrepOutput
	if err := json.Unmarshal([]byte(observation.Data), &output); err != nil {
		return nil
	}
	return &output
}

var sessionTemplate = template.Must(template.New("session-report").Funcs(template.FuncMap{
	"external": externalOutput,
	"grep":     grepOutput,
	"time":     func(value time.Time) string { return value.UTC().Format(time.RFC3339) },
}).Parse(`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>OWTF report - {{.Report.Session.Name}}</title>
  <style>
    :root { color-scheme: light; font-family: Inter, Arial, sans-serif; color: #18181b; background: #fafafa; }
    body { margin: 0; padding: 32px; }
    main { max-width: 1120px; margin: 0 auto; }
    h1, h2 { letter-spacing: -0.025em; }
    h1 { margin-bottom: 4px; }
    h2 { margin-top: 32px; font-size: 18px; }
    .muted { color: #71717a; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; margin: 24px 0; }
    .stat { border: 1px solid #e4e4e7; border-radius: 8px; background: white; padding: 12px; }
    .stat strong { display: block; font-size: 24px; }
    table { width: 100%; border-collapse: collapse; background: white; border: 1px solid #e4e4e7; }
    th, td { padding: 10px; border-bottom: 1px solid #e4e4e7; text-align: left; vertical-align: top; font-size: 13px; }
    th { background: #f4f4f5; }
    code { font-size: 12px; }
    a { color: #075985; }
    pre { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; }
    ul { margin: 6px 0 0; padding-left: 18px; }
  </style>
</head>
<body><main>
  <p class="muted">OWASP OWTF session report</p>
  <h1>{{.Report.Session.Name}}</h1>
  <p class="muted"><code>{{.Report.Session.ID}}</code> created {{time .Report.Session.CreatedAt}}</p>
  <section class="summary">
    <div class="stat"><strong>{{.Report.Summary.Targets}}</strong>Targets</div>
    <div class="stat"><strong>{{.Report.Summary.Runs}}</strong>Runs</div>
    <div class="stat"><strong>{{.Report.Summary.Tasks}}</strong>Tasks</div>
	    <div class="stat"><strong>{{.Report.Summary.Attempts}}</strong>Attempts</div>
	    <div class="stat"><strong>{{.Report.Summary.Succeeded}}</strong>Succeeded</div>
	    <div class="stat"><strong>{{.Report.Summary.Failed}}</strong>Failed</div>
	    <div class="stat"><strong>{{.Report.Summary.Transactions}}</strong>Transactions</div>
	    <div class="stat"><strong>{{.Report.Summary.Artifacts}}</strong>Artifacts</div>
	    <div class="stat"><strong>{{.Report.Summary.Findings}}</strong>Findings</div>
  </section>
  <h2>Targets</h2>
  <table><thead><tr><th>ID</th><th>Kind</th><th>Target</th></tr></thead><tbody>
  {{range .Report.Targets}}<tr><td><code>{{.ID}}</code></td><td>{{.Kind}}</td><td>{{.Value}}</td></tr>{{else}}<tr><td colspan="3">No targets</td></tr>{{end}}
  </tbody></table>
  <h2>Tasks</h2>
  <table><thead><tr><th>ID</th><th>Target</th><th>Plugin</th><th>Technique</th><th>Status</th><th>Rank</th><th>Notes</th><th>Error</th></tr></thead><tbody>
  {{range .Report.Tasks}}{{$review := index $.ReviewByTask .ID}}<tr><td><code>{{.ID}}</code></td><td><code>{{.TargetID}}</code></td><td>{{.PluginID}}</td><td>{{range .Techniques}}<div><code>{{.Code}}</code> {{.Title}}{{if .Hint}}<br><span class="muted">{{.Hint}}</span>{{end}}{{if .Reference}}<br><a href="{{.Reference}}">Reference</a>{{end}}</div>{{end}}</td><td>{{.Status}}</td><td>{{$review.Rank}}</td><td><pre>{{$review.Notes}}</pre></td><td>{{.Error}}</td></tr>{{else}}<tr><td colspan="8">No tasks</td></tr>{{end}}
  </tbody></table>
  <h2>Attempts</h2>
  <table><thead><tr><th>Task</th><th>Attempt</th><th>Status</th><th>Started</th><th>Error</th></tr></thead><tbody>
  {{range .Report.Attempts}}<tr><td><code>{{.TaskID}}</code></td><td>{{.AttemptNumber}}</td><td>{{.Status}}</td><td>{{time .StartedAt}}</td><td>{{.Error}}</td></tr>{{else}}<tr><td colspan="5">No attempts</td></tr>{{end}}
  </tbody></table>
  <h2>Observations</h2>
  <table><thead><tr><th>Technique</th><th>Kind</th><th>Output</th></tr></thead><tbody>
  {{range .Report.Observations}}<tr><td><code>{{.TechniqueCode}}</code></td><td>{{.Kind}}</td><td>{{$external := external .}}{{$grep := grep .}}{{if $external}}<div>{{$external.Guidance}}</div><ul>{{range $external.References}}<li><a href="{{.URL}}">{{.Title}}</a></li>{{end}}</ul>{{else if $grep}}<div>{{$grep.Title}}</div><ul>{{range $grep.TransactionIDs}}<li><a href="#transaction-{{.}}"><code>{{.}}</code></a></li>{{else}}<li class="muted">No matching transactions</li>{{end}}</ul>{{if $grep.Truncated}}<div class="muted">Match list truncated</div>{{end}}{{else}}<pre>{{.Data}}</pre>{{end}}</td></tr>{{else}}<tr><td colspan="3">No observations</td></tr>{{end}}
  </tbody></table>
  <h2>Findings</h2>
  <table><thead><tr><th>Severity</th><th>Technique</th><th>Title</th><th>Description</th></tr></thead><tbody>
  {{range .Report.Findings}}<tr><td>{{.Severity}}</td><td><code>{{.TechniqueCode}}</code></td><td>{{.Title}}</td><td>{{.Description}}</td></tr>{{else}}<tr><td colspan="4">No findings</td></tr>{{end}}
  </tbody></table>
  <h2>Transactions</h2>
  <table><thead><tr><th>ID</th><th>Method</th><th>URL</th><th>Status</th><th>Duration</th></tr></thead><tbody>
  {{range .Report.Transactions}}<tr id="transaction-{{.ID}}"><td><code>{{.ID}}</code></td><td>{{.Method}}</td><td>{{.URL}}</td><td>{{.StatusCode}}</td><td>{{.DurationMS}} ms</td></tr>{{else}}<tr><td colspan="5">No transactions</td></tr>{{end}}
  </tbody></table>
  <h2>Artifacts</h2>
	  <table><thead><tr><th>Name</th><th>Target</th><th>Task</th><th>Size</th><th>SHA-256</th></tr></thead><tbody>
	  {{range .Report.Artifacts}}<tr><td><a href="{{index $.ArtifactFiles .ID}}">{{.Name}}</a></td><td><code>{{.TargetID}}</code></td><td><code>{{.TaskID}}</code></td><td>{{.Size}}</td><td><code>{{.SHA256}}</code></td></tr>{{else}}<tr><td colspan="5">No artifacts</td></tr>{{end}}
  </tbody></table>
</main></body></html>`))
