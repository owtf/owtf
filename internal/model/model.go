package model

import (
	"bytes"
	"encoding/json"
	"time"
)

const (
	// RunQueued indicates that a run still has work waiting for a worker.
	RunQueued    = "queued"
	RunBlocked   = "blocked"
	RunRunning   = "running"
	RunSucceeded = "succeeded"
	RunFailed    = "failed"
	RunCancelled = "cancelled"

	TaskQueued    = "queued"
	TaskBlocked   = "blocked"
	TaskRunning   = "running"
	TaskSucceeded = "succeeded"
	TaskFailed    = "failed"
	TaskCancelled = "cancelled"

	ObservationKindExternalReferences = "external.references"
	ObservationKindGrepMatches        = "grep.matches"

	PluginOutputRankUnranked      = "unranked"
	PluginOutputRankPassing       = "passing"
	PluginOutputRankInformational = "informational"
	PluginOutputRankLow           = "low"
	PluginOutputRankMedium        = "medium"
	PluginOutputRankHigh          = "high"
	PluginOutputRankCritical      = "critical"
)

// Session is a named scan workspace containing targets and their execution
// history. It is unrelated to authentication or browser sessions.
type Session struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"created_at"`
}

// Target is one normalized URL, hostname, IP address, or CIDR in a session.
type Target struct {
	ID        string    `json:"id"`
	SessionID string    `json:"session_id"`
	Kind      string    `json:"kind"`
	Original  string    `json:"original"`
	Value     string    `json:"value"`
	Scope     bool      `json:"scope"`
	CreatedAt time.Time `json:"created_at"`
}

// TargetSearchResult reports both session and filtered totals for one bounded
// target query.
type TargetSearchResult struct {
	RecordsTotal    int      `json:"records_total"`
	RecordsFiltered int      `json:"records_filtered"`
	Data            []Target `json:"data"`
}

// PluginInput describes one non-secret value accepted by a plugin launch.
type PluginInput struct {
	Name        string   `yaml:"name" json:"name"`
	Type        string   `yaml:"type" json:"type"`
	Description string   `yaml:"description,omitempty" json:"description,omitempty"`
	Required    bool     `yaml:"required,omitempty" json:"required,omitempty"`
	Default     any      `yaml:"default,omitempty" json:"default,omitempty"`
	Choices     []string `yaml:"choices,omitempty" json:"choices,omitempty"`
	Minimum     *int64   `yaml:"minimum,omitempty" json:"minimum,omitempty"`
	Maximum     *int64   `yaml:"maximum,omitempty" json:"maximum,omitempty"`
}

// Technique is the OWTF test-group metadata shared by plugin type variants.
type Technique struct {
	Code      string `json:"code"`
	Title     string `json:"title"`
	Hint      string `json:"hint,omitempty"`
	Priority  int    `json:"priority"`
	Reference string `json:"reference,omitempty"`
}

// ExternalReference is one curated resource emitted by an external plugin.
type ExternalReference struct {
	Title string `yaml:"title" json:"title"`
	URL   string `yaml:"url" json:"url"`
}

// ExternalOutput is the stable observation payload produced by external
// plugins. It contains guidance only; executing it never contacts the target.
type ExternalOutput struct {
	Guidance   string              `json:"guidance"`
	References []ExternalReference `json:"references"`
}

// GrepOutput identifies the captured transactions matched by one declarative
// grep rule. Transaction IDs retain the evidence relationship without copying
// request or response content into the observation.
type GrepOutput struct {
	RuleID         string   `json:"rule_id"`
	Title          string   `json:"title"`
	Source         string   `json:"source"`
	TransactionIDs []string `json:"transaction_ids"`
	Truncated      bool     `json:"truncated,omitempty"`
}

// UnmarshalJSON accepts the code-only format used by early rewrite databases.
func (t *Technique) UnmarshalJSON(data []byte) error {
	if data = bytes.TrimSpace(data); len(data) != 0 && data[0] == '"' {
		var code string
		if err := json.Unmarshal(data, &code); err != nil {
			return err
		}
		*t = Technique{Code: code}
		return nil
	}
	type plain Technique
	return json.Unmarshal(data, (*plain)(t))
}

// Plugin is the indexed, operator-visible form of a plugin manifest.
type Plugin struct {
	ID           string        `json:"id"`
	Version      string        `json:"version"`
	Title        string        `json:"title"`
	Description  string        `json:"description"`
	Group        string        `json:"group"`
	Type         string        `json:"type"`
	Techniques   []Technique   `json:"techniques"`
	Inputs       []PluginInput `json:"inputs"`
	RuntimeType  string        `json:"runtime_type"`
	Availability string        `json:"availability"`
	Reason       string        `json:"reason,omitempty"`
	UpdatedAt    time.Time     `json:"updated_at"`
}

// Run groups the immutable set of tasks created by one launch request.
type Run struct {
	ID         string     `json:"id"`
	SessionID  string     `json:"session_id"`
	Profile    string     `json:"profile,omitempty"`
	Status     string     `json:"status"`
	CreatedAt  time.Time  `json:"created_at"`
	StartedAt  *time.Time `json:"started_at,omitempty"`
	FinishedAt *time.Time `json:"finished_at,omitempty"`
}

// Task is one plugin and target pair scheduled by a run.
type Task struct {
	ID         string         `json:"id"`
	RunID      string         `json:"run_id"`
	TargetID   string         `json:"target_id"`
	PluginID   string         `json:"plugin_id"`
	Techniques []Technique    `json:"techniques"`
	Inputs     map[string]any `json:"inputs"`
	Status     string         `json:"status"`
	Error      string         `json:"error,omitempty"`
	CreatedAt  time.Time      `json:"created_at"`
	StartedAt  *time.Time     `json:"started_at,omitempty"`
	EndedAt    *time.Time     `json:"ended_at,omitempty"`
}

// TaskExecution contains the task, its current attempt, and the resolved target
// needed by the runner.
type TaskExecution struct {
	Task
	AttemptID      string `json:"attempt_id"`
	AttemptNumber  int    `json:"attempt_number"`
	Target         Target `json:"target"`
	PluginSnapshot string `json:"-"`
}

// TaskAttempt records one execution of a durable worklist task.
type TaskAttempt struct {
	ID            string     `json:"id"`
	TaskID        string     `json:"task_id"`
	AttemptNumber int        `json:"attempt_number"`
	Status        string     `json:"status"`
	StartedAt     time.Time  `json:"started_at"`
	EndedAt       *time.Time `json:"ended_at,omitempty"`
	Error         string     `json:"error,omitempty"`
}

// TaskEvent is one ordered lifecycle, stdout, or stderr record for a task.
type TaskEvent struct {
	ID        int64     `json:"id"`
	TaskID    string    `json:"task_id"`
	AttemptID string    `json:"attempt_id,omitempty"`
	Stream    string    `json:"stream"`
	Message   string    `json:"message"`
	CreatedAt time.Time `json:"created_at"`
}

// PluginOutputReview contains the operator-owned review of one immutable task
// output. OWTF has no user records; the deployment boundary owns actor
// attribution when it is required.
type PluginOutputReview struct {
	TaskID    string     `json:"task_id"`
	Rank      string     `json:"rank"`
	Notes     string     `json:"notes"`
	UpdatedAt *time.Time `json:"updated_at,omitempty"`
}

// Worker reports the live state and process-lifetime counters of one bounded
// runner worker.
type Worker struct {
	ID            string     `json:"id"`
	Status        string     `json:"status"`
	TaskID        string     `json:"task_id,omitempty"`
	TargetID      string     `json:"target_id,omitempty"`
	PluginID      string     `json:"plugin_id,omitempty"`
	TaskStartedAt *time.Time `json:"task_started_at,omitempty"`
	Completed     int        `json:"completed"`
	Failed        int        `json:"failed"`
	Cancelled     int        `json:"cancelled"`
}

// Artifact describes immutable evidence stored outside SQLite.
type Artifact struct {
	ID        string    `json:"id"`
	TaskID    string    `json:"task_id,omitempty"`
	TargetID  string    `json:"target_id"`
	Name      string    `json:"name"`
	MediaType string    `json:"media_type"`
	Size      int64     `json:"size"`
	SHA256    string    `json:"sha256"`
	Path      string    `json:"path"`
	CreatedAt time.Time `json:"created_at"`
}

// Transaction records one HTTP request and response associated with a target.
type Transaction struct {
	ID                     string    `json:"id"`
	TaskID                 string    `json:"task_id,omitempty"`
	TargetID               string    `json:"target_id"`
	Method                 string    `json:"method"`
	URL                    string    `json:"url"`
	RequestHeaders         string    `json:"request_headers"`
	StatusCode             int       `json:"status_code"`
	ResponseHeaders        string    `json:"response_headers"`
	SourceArtifactID       string    `json:"source_artifact_id,omitempty"`
	RequestBodyArtifactID  string    `json:"request_body_artifact_id,omitempty"`
	ResponseBodyArtifactID string    `json:"response_body_artifact_id,omitempty"`
	DurationMS             int64     `json:"duration_ms"`
	CreatedAt              time.Time `json:"created_at"`
}

// TransactionSearchResult reports unfiltered and filtered totals for one
// bounded transaction query.
type TransactionSearchResult struct {
	RecordsTotal    int           `json:"records_total"`
	RecordsFiltered int           `json:"records_filtered"`
	Data            []Transaction `json:"data"`
}

// Observation is a tool-produced fact that has not been promoted to a finding.
type Observation struct {
	ID            string    `json:"id"`
	TaskID        string    `json:"task_id"`
	TargetID      string    `json:"target_id"`
	TechniqueCode string    `json:"technique_code"`
	Kind          string    `json:"kind"`
	Data          string    `json:"data"`
	CreatedAt     time.Time `json:"created_at"`
}

// Finding is a reviewable security conclusion with evidence provenance.
type Finding struct {
	ID            string    `json:"id"`
	TaskID        string    `json:"task_id"`
	TargetID      string    `json:"target_id"`
	TechniqueCode string    `json:"technique_code"`
	Title         string    `json:"title"`
	Severity      string    `json:"severity"`
	Description   string    `json:"description"`
	CreatedAt     time.Time `json:"created_at"`
}

// ReportSummary contains truthful counts derived from persisted report records.
type ReportSummary struct {
	Targets      int `json:"targets"`
	Runs         int `json:"runs"`
	Tasks        int `json:"tasks"`
	Attempts     int `json:"attempts"`
	Queued       int `json:"queued"`
	Blocked      int `json:"blocked"`
	Running      int `json:"running"`
	Succeeded    int `json:"succeeded"`
	Failed       int `json:"failed"`
	Cancelled    int `json:"cancelled"`
	Transactions int `json:"transactions"`
	Artifacts    int `json:"artifacts"`
	Observations int `json:"observations"`
	Findings     int `json:"findings"`
}

// TargetReport is the complete retained evidence view for one target.
type TargetReport struct {
	Target              Target               `json:"target"`
	Tasks               []Task               `json:"tasks"`
	PluginOutputReviews []PluginOutputReview `json:"plugin_output_reviews"`
	Attempts            []TaskAttempt        `json:"attempts"`
	Events              []TaskEvent          `json:"events"`
	Artifacts           []Artifact           `json:"artifacts"`
	Transactions        []Transaction        `json:"transactions"`
	Observations        []Observation        `json:"observations"`
	Findings            []Finding            `json:"findings"`
}

// SessionReport is the complete retained execution and evidence view for one
// OWTF session.
type SessionReport struct {
	Session             Session              `json:"session"`
	Summary             ReportSummary        `json:"summary"`
	Targets             []Target             `json:"targets"`
	Runs                []Run                `json:"runs"`
	Tasks               []Task               `json:"tasks"`
	PluginOutputReviews []PluginOutputReview `json:"plugin_output_reviews"`
	Attempts            []TaskAttempt        `json:"attempts"`
	Events              []TaskEvent          `json:"events"`
	Artifacts           []Artifact           `json:"artifacts"`
	Transactions        []Transaction        `json:"transactions"`
	Observations        []Observation        `json:"observations"`
	Findings            []Finding            `json:"findings"`
}
