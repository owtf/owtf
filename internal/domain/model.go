package domain

import "time"

const (
	// RunQueued indicates that a run still has work waiting for a worker.
	RunQueued    = "queued"
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
	CreatedAt time.Time `json:"created_at"`
}

// Plugin is the indexed, operator-visible form of a plugin manifest.
type Plugin struct {
	ID           string    `json:"id"`
	Version      string    `json:"version"`
	Title        string    `json:"title"`
	Description  string    `json:"description"`
	Variant      string    `json:"variant"`
	Techniques   []string  `json:"techniques"`
	RuntimeType  string    `json:"runtime_type"`
	Availability string    `json:"availability"`
	Reason       string    `json:"reason,omitempty"`
	UpdatedAt    time.Time `json:"updated_at"`
}

// Run groups the immutable set of tasks created by one launch request.
type Run struct {
	ID         string     `json:"id"`
	SessionID  string     `json:"session_id"`
	Status     string     `json:"status"`
	CreatedAt  time.Time  `json:"created_at"`
	StartedAt  *time.Time `json:"started_at,omitempty"`
	FinishedAt *time.Time `json:"finished_at,omitempty"`
}

// Task is one plugin and target pair scheduled by a run.
type Task struct {
	ID        string     `json:"id"`
	RunID     string     `json:"run_id"`
	TargetID  string     `json:"target_id"`
	PluginID  string     `json:"plugin_id"`
	Status    string     `json:"status"`
	Error     string     `json:"error,omitempty"`
	CreatedAt time.Time  `json:"created_at"`
	StartedAt *time.Time `json:"started_at,omitempty"`
	EndedAt   *time.Time `json:"ended_at,omitempty"`
}

// TaskExecution contains the task, its current attempt, and the resolved target
// needed by the runner.
type TaskExecution struct {
	Task
	AttemptID     string `json:"attempt_id"`
	AttemptNumber int    `json:"attempt_number"`
	Target        Target `json:"target"`
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
	TaskID    string    `json:"task_id"`
	Name      string    `json:"name"`
	MediaType string    `json:"media_type"`
	Size      int64     `json:"size"`
	SHA256    string    `json:"sha256"`
	Path      string    `json:"path"`
	CreatedAt time.Time `json:"created_at"`
}

// HTTPExchange records request and response metadata captured by a plugin.
type HTTPExchange struct {
	ID                     string    `json:"id"`
	TaskID                 string    `json:"task_id"`
	TargetID               string    `json:"target_id"`
	Method                 string    `json:"method"`
	URL                    string    `json:"url"`
	RequestHeaders         string    `json:"request_headers"`
	StatusCode             int       `json:"status_code"`
	ResponseHeaders        string    `json:"response_headers"`
	ResponseBodyArtifactID string    `json:"response_body_artifact_id,omitempty"`
	DurationMS             int64     `json:"duration_ms"`
	CreatedAt              time.Time `json:"created_at"`
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

// TargetReport is the complete retained evidence view for one target.
type TargetReport struct {
	Target       Target         `json:"target"`
	Tasks        []Task         `json:"tasks"`
	Events       []TaskEvent    `json:"events"`
	Artifacts    []Artifact     `json:"artifacts"`
	Transactions []HTTPExchange `json:"transactions"`
	Observations []Observation  `json:"observations"`
	Findings     []Finding      `json:"findings"`
}
