package store

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	_ "github.com/mattn/go-sqlite3"
	"github.com/owtf/owtf/internal/domain"
	targetvalue "github.com/owtf/owtf/internal/target"
)

var (
	// ErrNotFound indicates that a requested public ID does not exist.
	ErrNotFound = errors.New("not found")
	// ErrTaskNotRunning indicates that a terminal task cannot transition again.
	ErrTaskNotRunning = errors.New("task is not running")
)

// TaskSpec is one validated target/plugin pair used to create a durable task.
type TaskSpec struct {
	TargetID       string
	PluginID       string
	PluginVersion  string
	PluginSnapshot string
}

// Store is a serialized SQLite connection for OWTF control-plane state.
type Store struct {
	db *sql.DB
}

// Open creates or migrates the SQLite database at path.
func Open(path string) (*Store, error) {
	if err := ensureParent(path); err != nil {
		return nil, err
	}
	dsn := fmt.Sprintf("file:%s?_foreign_keys=on&_busy_timeout=5000&_journal_mode=WAL", path)
	db, err := sql.Open("sqlite3", dsn)
	if err != nil {
		return nil, fmt.Errorf("open sqlite database: %w", err)
	}
	db.SetMaxOpenConns(1)
	store := &Store{db: db}
	if err := store.migrate(context.Background()); err != nil {
		db.Close()
		return nil, err
	}
	return store, nil
}

func ensureParent(path string) error {
	parent := filepath.Dir(path)
	if parent == "." {
		return nil
	}
	return os.MkdirAll(parent, 0o750)
}

// Close releases the SQLite connection.
func (s *Store) Close() error { return s.db.Close() }

func (s *Store) migrate(ctx context.Context) error {
	const schema = `
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS targets (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    original TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(session_id, value)
);
CREATE TABLE IF NOT EXISTS techniques (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'supported'
);
CREATE TABLE IF NOT EXISTS plugins (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    variant TEXT NOT NULL,
    techniques_json TEXT NOT NULL,
    runtime_type TEXT NOT NULL,
    availability TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    plugin_id TEXT NOT NULL,
    plugin_version TEXT NOT NULL,
    plugin_snapshot TEXT NOT NULL,
    status TEXT NOT NULL,
    error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT
);
CREATE INDEX IF NOT EXISTS tasks_status_idx ON tasks(status, id);
CREATE INDEX IF NOT EXISTS tasks_target_idx ON tasks(target_id, id);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    error TEXT NOT NULL DEFAULT '',
    UNIQUE(task_id, attempt_number)
);
CREATE TABLE IF NOT EXISTS task_events (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    attempt_id INTEGER REFERENCES attempts(id) ON DELETE CASCADE,
    stream TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS task_events_task_idx ON task_events(task_id, id);
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    media_type TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    path TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS http_exchanges (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    request_headers TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_headers TEXT NOT NULL,
    response_body_artifact_id INTEGER REFERENCES artifacts(id) ON DELETE SET NULL,
    duration_ms INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    technique_code TEXT NOT NULL,
    kind TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    technique_code TEXT NOT NULL,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL
);`
	if _, err := s.db.ExecContext(ctx, schema); err != nil {
		return fmt.Errorf("migrate database: %w", err)
	}
	if _, err := s.db.ExecContext(ctx, `DELETE FROM runs WHERE NOT EXISTS (SELECT 1 FROM tasks WHERE tasks.run_id=runs.id)`); err != nil {
		return fmt.Errorf("prune empty runs: %w", err)
	}
	return nil
}

// CreateSession creates a named scan workspace.
func (s *Store) CreateSession(ctx context.Context, name string) (domain.Session, error) {
	name = strings.TrimSpace(name)
	if name == "" {
		name = "Default session"
	}
	session := domain.Session{ID: newID("ses"), Name: name, CreatedAt: time.Now().UTC()}
	_, err := s.db.ExecContext(ctx, `INSERT INTO sessions(public_id, name, created_at) VALUES(?, ?, ?)`,
		session.ID, session.Name, formatTime(session.CreatedAt))
	if err != nil {
		return domain.Session{}, fmt.Errorf("create session: %w", err)
	}
	return session, nil
}

// ListSessions returns sessions newest first.
func (s *Store) ListSessions(ctx context.Context) ([]domain.Session, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT public_id, name, created_at FROM sessions ORDER BY id DESC`)
	if err != nil {
		return nil, fmt.Errorf("list sessions: %w", err)
	}
	defer rows.Close()
	sessions := make([]domain.Session, 0)
	for rows.Next() {
		var item domain.Session
		var created string
		if err := rows.Scan(&item.ID, &item.Name, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		sessions = append(sessions, item)
	}
	return sessions, rows.Err()
}

// GetSession returns one session by public ID.
func (s *Store) GetSession(ctx context.Context, id string) (domain.Session, error) {
	var item domain.Session
	var created string
	err := s.db.QueryRowContext(ctx, `SELECT public_id, name, created_at FROM sessions WHERE public_id = ?`, id).
		Scan(&item.ID, &item.Name, &created)
	if errors.Is(err, sql.ErrNoRows) {
		return domain.Session{}, ErrNotFound
	}
	if err != nil {
		return domain.Session{}, err
	}
	item.CreatedAt = parseTime(created)
	return item, nil
}

// AddTargetsResult separates newly stored targets from normalized duplicates.
type AddTargetsResult struct {
	Created    []domain.Target `json:"created"`
	Duplicates []string        `json:"duplicates"`
}

// AddTargets stores normalized targets in a session and reports duplicates.
func (s *Store) AddTargets(ctx context.Context, sessionID string, targets []targetvalue.Normalized) (AddTargetsResult, error) {
	var sessionPK int64
	if err := s.db.QueryRowContext(ctx, `SELECT id FROM sessions WHERE public_id = ?`, sessionID).Scan(&sessionPK); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return AddTargetsResult{}, ErrNotFound
		}
		return AddTargetsResult{}, err
	}
	result := AddTargetsResult{Created: []domain.Target{}, Duplicates: []string{}}
	now := time.Now().UTC()
	for _, normalized := range targets {
		item := domain.Target{
			ID: newID("tgt"), SessionID: sessionID, Kind: normalized.Kind,
			Original: normalized.Original, Value: normalized.Value, CreatedAt: now,
		}
		_, err := s.db.ExecContext(ctx, `
INSERT INTO targets(public_id, session_id, kind, original, value, created_at)
VALUES(?, ?, ?, ?, ?, ?)`, item.ID, sessionPK, item.Kind, item.Original, item.Value, formatTime(item.CreatedAt))
		if err != nil {
			if strings.Contains(err.Error(), "UNIQUE constraint failed") {
				result.Duplicates = append(result.Duplicates, normalized.Original)
				continue
			}
			return AddTargetsResult{}, fmt.Errorf("add target %q: %w", normalized.Original, err)
		}
		result.Created = append(result.Created, item)
	}
	return result, nil
}

// ListTargets returns all targets in a session, newest first.
func (s *Store) ListTargets(ctx context.Context, sessionID string) ([]domain.Target, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT t.public_id, s.public_id, t.kind, t.original, t.value, t.created_at
FROM targets t JOIN sessions s ON s.id = t.session_id
WHERE s.public_id = ? ORDER BY t.id DESC`, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	targets := make([]domain.Target, 0)
	for rows.Next() {
		item, err := scanTarget(rows)
		if err != nil {
			return nil, err
		}
		targets = append(targets, item)
	}
	return targets, rows.Err()
}

// GetTarget returns one target by public ID.
func (s *Store) GetTarget(ctx context.Context, id string) (domain.Target, error) {
	row := s.db.QueryRowContext(ctx, `
SELECT t.public_id, s.public_id, t.kind, t.original, t.value, t.created_at
FROM targets t JOIN sessions s ON s.id = t.session_id WHERE t.public_id = ?`, id)
	item, err := scanTarget(row)
	if errors.Is(err, sql.ErrNoRows) {
		return domain.Target{}, ErrNotFound
	}
	return item, err
}

// DeleteTarget removes a target and its dependent execution evidence.
func (s *Store) DeleteTarget(ctx context.Context, id string) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	result, err := tx.ExecContext(ctx, `DELETE FROM targets WHERE public_id = ?`, id)
	if err != nil {
		return err
	}
	if count, _ := result.RowsAffected(); count == 0 {
		return ErrNotFound
	}
	if _, err := tx.ExecContext(ctx, `DELETE FROM runs WHERE NOT EXISTS (SELECT 1 FROM tasks WHERE tasks.run_id=runs.id)`); err != nil {
		return err
	}
	return tx.Commit()
}

type rowScanner interface {
	Scan(dest ...any) error
}

func scanTarget(row rowScanner) (domain.Target, error) {
	var item domain.Target
	var created string
	err := row.Scan(&item.ID, &item.SessionID, &item.Kind, &item.Original, &item.Value, &created)
	item.CreatedAt = parseTime(created)
	return item, err
}

// ReplacePlugins atomically synchronizes the indexed plugin catalog.
func (s *Store) ReplacePlugins(ctx context.Context, plugins []domain.Plugin) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if _, err := tx.ExecContext(ctx, `DELETE FROM plugins`); err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `DELETE FROM techniques`); err != nil {
		return err
	}
	for _, item := range plugins {
		techniquesJSON, _ := json.Marshal(item.Techniques)
		updated := time.Now().UTC()
		_, err = tx.ExecContext(ctx, `
INSERT INTO plugins(id, version, title, description, variant, techniques_json, runtime_type, availability, reason, updated_at)
VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, item.ID, item.Version, item.Title, item.Description, item.Variant,
			string(techniquesJSON), item.RuntimeType, item.Availability, item.Reason, formatTime(updated))
		if err != nil {
			return err
		}
		for _, technique := range item.Techniques {
			if _, err := tx.ExecContext(ctx, `INSERT INTO techniques(code, title) VALUES(?, ?) ON CONFLICT(code) DO NOTHING`, technique, technique); err != nil {
				return err
			}
		}
	}
	return tx.Commit()
}

// ListPlugins returns the current indexed catalog ordered by plugin ID.
func (s *Store) ListPlugins(ctx context.Context) ([]domain.Plugin, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT id, version, title, description, variant, techniques_json, runtime_type, availability, reason, updated_at
FROM plugins ORDER BY id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	plugins := make([]domain.Plugin, 0)
	for rows.Next() {
		var item domain.Plugin
		var techniquesJSON, updated string
		if err := rows.Scan(&item.ID, &item.Version, &item.Title, &item.Description, &item.Variant,
			&techniquesJSON, &item.RuntimeType, &item.Availability, &item.Reason, &updated); err != nil {
			return nil, err
		}
		_ = json.Unmarshal([]byte(techniquesJSON), &item.Techniques)
		item.UpdatedAt = parseTime(updated)
		plugins = append(plugins, item)
	}
	return plugins, rows.Err()
}

// CreateRun atomically creates an immutable launch record and its tasks.
func (s *Store) CreateRun(ctx context.Context, sessionID string, specs []TaskSpec) (domain.Run, []domain.Task, error) {
	if len(specs) == 0 {
		return domain.Run{}, nil, fmt.Errorf("at least one task is required")
	}
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return domain.Run{}, nil, err
	}
	defer tx.Rollback()
	var sessionPK int64
	if err := tx.QueryRowContext(ctx, `SELECT id FROM sessions WHERE public_id = ?`, sessionID).Scan(&sessionPK); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return domain.Run{}, nil, ErrNotFound
		}
		return domain.Run{}, nil, err
	}
	now := time.Now().UTC()
	run := domain.Run{ID: newID("run"), SessionID: sessionID, Status: domain.RunQueued, CreatedAt: now}
	result, err := tx.ExecContext(ctx, `INSERT INTO runs(public_id, session_id, status, created_at) VALUES(?, ?, ?, ?)`,
		run.ID, sessionPK, run.Status, formatTime(run.CreatedAt))
	if err != nil {
		return domain.Run{}, nil, err
	}
	runPK, _ := result.LastInsertId()
	tasks := make([]domain.Task, 0, len(specs))
	for _, spec := range specs {
		var targetPK int64
		if err := tx.QueryRowContext(ctx, `SELECT id FROM targets WHERE public_id = ? AND session_id = ?`, spec.TargetID, sessionPK).Scan(&targetPK); err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				return domain.Run{}, nil, fmt.Errorf("target %s does not belong to session", spec.TargetID)
			}
			return domain.Run{}, nil, err
		}
		task := domain.Task{
			ID: newID("tsk"), RunID: run.ID, TargetID: spec.TargetID, PluginID: spec.PluginID,
			Status: domain.TaskQueued, CreatedAt: now,
		}
		_, err := tx.ExecContext(ctx, `
INSERT INTO tasks(public_id, run_id, target_id, plugin_id, plugin_version, plugin_snapshot, status, created_at)
VALUES(?, ?, ?, ?, ?, ?, ?, ?)`, task.ID, runPK, targetPK, spec.PluginID, spec.PluginVersion,
			spec.PluginSnapshot, task.Status, formatTime(task.CreatedAt))
		if err != nil {
			return domain.Run{}, nil, err
		}
		tasks = append(tasks, task)
	}
	if err := tx.Commit(); err != nil {
		return domain.Run{}, nil, err
	}
	return run, tasks, nil
}

// RecoverTasks marks interrupted attempts failed and returns their task IDs for
// a new queued attempt.
func (s *Store) RecoverTasks(ctx context.Context) ([]string, error) {
	now := formatTime(time.Now().UTC())
	if _, err := s.db.ExecContext(ctx, `
UPDATE attempts SET status = ?, ended_at = ?, error = 'server restarted during execution'
WHERE status = ?`, domain.TaskFailed, now, domain.TaskRunning); err != nil {
		return nil, err
	}
	if _, err := s.db.ExecContext(ctx, `
UPDATE tasks SET status = ?, error = 'recovered after server restart', started_at = NULL
WHERE status = ?`, domain.TaskQueued, domain.TaskRunning); err != nil {
		return nil, err
	}
	rows, err := s.db.QueryContext(ctx, `SELECT public_id FROM tasks WHERE status = ? ORDER BY id`, domain.TaskQueued)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	ids := make([]string, 0)
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			return nil, err
		}
		ids = append(ids, id)
	}
	return ids, rows.Err()
}

// StartTask claims a queued task and creates its next attempt transactionally.
func (s *Store) StartTask(ctx context.Context, taskID string) (domain.TaskExecution, error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return domain.TaskExecution{}, err
	}
	defer tx.Rollback()
	var taskPK, runPK, targetPK int64
	var execution domain.TaskExecution
	var targetCreated, taskCreated string
	err = tx.QueryRowContext(ctx, `
SELECT t.id, t.public_id, r.id, r.public_id, tg.id, tg.public_id, a.public_id,
       tg.kind, tg.original, tg.value, tg.created_at, t.plugin_id, t.status, t.created_at
FROM tasks t
JOIN runs r ON r.id = t.run_id
JOIN targets tg ON tg.id = t.target_id
JOIN sessions a ON a.id = tg.session_id
WHERE t.public_id = ?`, taskID).Scan(
		&taskPK, &execution.ID, &runPK, &execution.RunID, &targetPK, &execution.Target.ID,
		&execution.Target.SessionID, &execution.Target.Kind, &execution.Target.Original,
		&execution.Target.Value, &targetCreated, &execution.PluginID, &execution.Status, &taskCreated,
	)
	if errors.Is(err, sql.ErrNoRows) {
		return domain.TaskExecution{}, ErrNotFound
	}
	if err != nil {
		return domain.TaskExecution{}, err
	}
	if execution.Status != domain.TaskQueued {
		return domain.TaskExecution{}, fmt.Errorf("%w: task is %s", ErrTaskNotRunning, execution.Status)
	}
	now := time.Now().UTC()
	execution.Target.CreatedAt = parseTime(targetCreated)
	execution.CreatedAt = parseTime(taskCreated)
	execution.TargetID = execution.Target.ID
	execution.Status = domain.TaskRunning
	execution.StartedAt = &now
	var attemptNumber int
	if err := tx.QueryRowContext(ctx, `SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM attempts WHERE task_id = ?`, taskPK).Scan(&attemptNumber); err != nil {
		return domain.TaskExecution{}, err
	}
	execution.AttemptID = newID("att")
	execution.AttemptNumber = attemptNumber
	if _, err := tx.ExecContext(ctx, `UPDATE tasks SET status = ?, error = '', started_at = ?, ended_at = NULL WHERE id = ?`,
		domain.TaskRunning, formatTime(now), taskPK); err != nil {
		return domain.TaskExecution{}, err
	}
	if _, err := tx.ExecContext(ctx, `INSERT INTO attempts(public_id, task_id, attempt_number, status, started_at) VALUES(?, ?, ?, ?, ?)`,
		execution.AttemptID, taskPK, attemptNumber, domain.TaskRunning, formatTime(now)); err != nil {
		return domain.TaskExecution{}, err
	}
	if _, err := tx.ExecContext(ctx, `UPDATE runs SET status = ?, started_at = COALESCE(started_at, ?) WHERE id = ?`,
		domain.RunRunning, formatTime(now), runPK); err != nil {
		return domain.TaskExecution{}, err
	}
	return execution, tx.Commit()
}

// AddTaskEvent appends ordered diagnostic or lifecycle output to a task.
func (s *Store) AddTaskEvent(ctx context.Context, taskID, attemptID, stream, message string) error {
	_, err := s.db.ExecContext(ctx, `
INSERT INTO task_events(task_id, attempt_id, stream, message, created_at)
SELECT t.id, a.id, ?, ?, ? FROM tasks t
LEFT JOIN attempts a ON a.public_id = ? AND a.task_id = t.id
WHERE t.public_id = ?`, stream, message, formatTime(time.Now().UTC()), attemptID, taskID)
	return err
}

// CompleteTask atomically stores structured output and marks a task successful.
func (s *Store) CompleteTask(ctx context.Context, execution domain.TaskExecution, artifacts []domain.Artifact,
	exchanges []domain.HTTPExchange, observations []domain.Observation, findings []domain.Finding) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var taskPK, runPK, targetPK, attemptPK int64
	var taskStatus string
	if err := tx.QueryRowContext(ctx, `
SELECT t.id, t.run_id, t.target_id, a.id, t.status FROM tasks t JOIN attempts a ON a.task_id=t.id
WHERE t.public_id=? AND a.public_id=?`, execution.ID, execution.AttemptID).
		Scan(&taskPK, &runPK, &targetPK, &attemptPK, &taskStatus); err != nil {
		return err
	}
	if taskStatus != domain.TaskRunning {
		return ErrTaskNotRunning
	}
	artifactPKs := make(map[string]int64)
	for _, item := range artifacts {
		result, err := tx.ExecContext(ctx, `
INSERT INTO artifacts(public_id, task_id, name, media_type, size, sha256, path, created_at)
VALUES(?, ?, ?, ?, ?, ?, ?, ?)`, item.ID, taskPK, item.Name, item.MediaType, item.Size, item.SHA256,
			item.Path, formatTime(item.CreatedAt))
		if err != nil {
			return err
		}
		artifactPKs[item.ID], _ = result.LastInsertId()
	}
	for _, item := range exchanges {
		var artifactPK any
		if item.ResponseBodyArtifactID != "" {
			artifactPK = artifactPKs[item.ResponseBodyArtifactID]
		}
		_, err := tx.ExecContext(ctx, `
INSERT INTO http_exchanges(public_id, task_id, target_id, method, url, request_headers, status_code,
response_headers, response_body_artifact_id, duration_ms, created_at)
VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, item.ID, taskPK, targetPK, item.Method, item.URL,
			item.RequestHeaders, item.StatusCode, item.ResponseHeaders, artifactPK, item.DurationMS, formatTime(item.CreatedAt))
		if err != nil {
			return err
		}
	}
	for _, item := range observations {
		_, err := tx.ExecContext(ctx, `
INSERT INTO observations(public_id, task_id, target_id, technique_code, kind, data, created_at)
VALUES(?, ?, ?, ?, ?, ?, ?)`, item.ID, taskPK, targetPK, item.TechniqueCode, item.Kind, item.Data, formatTime(item.CreatedAt))
		if err != nil {
			return err
		}
	}
	for _, item := range findings {
		_, err := tx.ExecContext(ctx, `
INSERT INTO findings(public_id, task_id, target_id, technique_code, title, severity, description, created_at)
VALUES(?, ?, ?, ?, ?, ?, ?, ?)`, item.ID, taskPK, targetPK, item.TechniqueCode, item.Title,
			item.Severity, item.Description, formatTime(item.CreatedAt))
		if err != nil {
			return err
		}
	}
	now := time.Now().UTC()
	if _, err := tx.ExecContext(ctx, `UPDATE attempts SET status=?, ended_at=? WHERE id=?`, domain.TaskSucceeded, formatTime(now), attemptPK); err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `UPDATE tasks SET status=?, ended_at=? WHERE id=?`, domain.TaskSucceeded, formatTime(now), taskPK); err != nil {
		return err
	}
	if err := refreshRunStatus(ctx, tx, runPK, now); err != nil {
		return err
	}
	return tx.Commit()
}

// FailTask records a terminal execution error and refreshes its parent run.
func (s *Store) FailTask(ctx context.Context, execution domain.TaskExecution, taskError error) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var taskPK, runPK, attemptPK int64
	var taskStatus string
	if err := tx.QueryRowContext(ctx, `
SELECT t.id, t.run_id, a.id, t.status FROM tasks t JOIN attempts a ON a.task_id=t.id
WHERE t.public_id=? AND a.public_id=?`, execution.ID, execution.AttemptID).
		Scan(&taskPK, &runPK, &attemptPK, &taskStatus); err != nil {
		return err
	}
	if taskStatus != domain.TaskRunning {
		return ErrTaskNotRunning
	}
	now := time.Now().UTC()
	message := taskError.Error()
	if _, err := tx.ExecContext(ctx, `UPDATE attempts SET status=?, ended_at=?, error=? WHERE id=?`, domain.TaskFailed, formatTime(now), message, attemptPK); err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `UPDATE tasks SET status=?, ended_at=?, error=? WHERE id=?`, domain.TaskFailed, formatTime(now), message, taskPK); err != nil {
		return err
	}
	if err := refreshRunStatus(ctx, tx, runPK, now); err != nil {
		return err
	}
	return tx.Commit()
}

func refreshRunStatus(ctx context.Context, tx *sql.Tx, runPK int64, now time.Time) error {
	var pending, failed, cancelled int
	if err := tx.QueryRowContext(ctx, `
SELECT SUM(CASE WHEN status IN ('queued','running') THEN 1 ELSE 0 END),
       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END),
       SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END)
FROM tasks WHERE run_id = ?`, runPK).Scan(&pending, &failed, &cancelled); err != nil {
		return err
	}
	if pending != 0 {
		return nil
	}
	status := domain.RunSucceeded
	if failed > 0 {
		status = domain.RunFailed
	} else if cancelled > 0 {
		status = domain.RunCancelled
	}
	_, err := tx.ExecContext(ctx, `UPDATE runs SET status=?, finished_at=? WHERE id=?`, status, formatTime(now), runPK)
	return err
}

// ListTasks returns worklist tasks, optionally filtered by session and status.
func (s *Store) ListTasks(ctx context.Context, sessionID, status string) ([]domain.Task, error) {
	query := `
SELECT t.public_id, r.public_id, tg.public_id, t.plugin_id, t.status, t.error,
       t.created_at, t.started_at, t.ended_at
FROM tasks t JOIN runs r ON r.id=t.run_id JOIN targets tg ON tg.id=t.target_id
JOIN sessions s ON s.id=r.session_id WHERE 1=1`
	var args []any
	if sessionID != "" {
		query += ` AND s.public_id=?`
		args = append(args, sessionID)
	}
	if status != "" {
		query += ` AND t.status=?`
		args = append(args, status)
	}
	query += ` ORDER BY t.id DESC`
	rows, err := s.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	tasks := make([]domain.Task, 0)
	for rows.Next() {
		item, err := scanTask(rows)
		if err != nil {
			return nil, err
		}
		tasks = append(tasks, item)
	}
	return tasks, rows.Err()
}

// GetTask returns one task by public ID.
func (s *Store) GetTask(ctx context.Context, taskID string) (domain.Task, error) {
	row := s.db.QueryRowContext(ctx, `
SELECT t.public_id, r.public_id, tg.public_id, t.plugin_id, t.status, t.error,
       t.created_at, t.started_at, t.ended_at
FROM tasks t JOIN runs r ON r.id=t.run_id JOIN targets tg ON tg.id=t.target_id
WHERE t.public_id=?`, taskID)
	item, err := scanTask(row)
	if errors.Is(err, sql.ErrNoRows) {
		return domain.Task{}, ErrNotFound
	}
	return item, err
}

// CancelTask records operator cancellation for queued or running work.
func (s *Store) CancelTask(ctx context.Context, taskID string) (domain.Task, error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return domain.Task{}, err
	}
	defer tx.Rollback()
	var taskPK, runPK int64
	var status string
	if err := tx.QueryRowContext(ctx, `SELECT id, run_id, status FROM tasks WHERE public_id=?`, taskID).
		Scan(&taskPK, &runPK, &status); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return domain.Task{}, ErrNotFound
		}
		return domain.Task{}, err
	}
	if status == domain.TaskQueued || status == domain.TaskRunning {
		now := time.Now().UTC()
		if _, err := tx.ExecContext(ctx, `
UPDATE tasks SET status=?, error='cancelled by operator', ended_at=? WHERE id=?`,
			domain.TaskCancelled, formatTime(now), taskPK); err != nil {
			return domain.Task{}, err
		}
		if _, err := tx.ExecContext(ctx, `
UPDATE attempts SET status=?, error='cancelled by operator', ended_at=?
WHERE task_id=? AND status=?`, domain.TaskCancelled, formatTime(now), taskPK, domain.TaskRunning); err != nil {
			return domain.Task{}, err
		}
		if err := refreshRunStatus(ctx, tx, runPK, now); err != nil {
			return domain.Task{}, err
		}
	}
	if err := tx.Commit(); err != nil {
		return domain.Task{}, err
	}
	return s.GetTask(ctx, taskID)
}

func scanTask(row rowScanner) (domain.Task, error) {
	var item domain.Task
	var created string
	var started, ended sql.NullString
	err := row.Scan(&item.ID, &item.RunID, &item.TargetID, &item.PluginID, &item.Status, &item.Error,
		&created, &started, &ended)
	item.CreatedAt = parseTime(created)
	item.StartedAt = parseNullTime(started)
	item.EndedAt = parseNullTime(ended)
	return item, err
}

// ListTaskEvents returns task output in insertion order.
func (s *Store) ListTaskEvents(ctx context.Context, taskID string) ([]domain.TaskEvent, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT e.id, t.public_id, COALESCE(a.public_id,''), e.stream, e.message, e.created_at
FROM task_events e JOIN tasks t ON t.id=e.task_id LEFT JOIN attempts a ON a.id=e.attempt_id
WHERE t.public_id=? ORDER BY e.id`, taskID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	events := make([]domain.TaskEvent, 0)
	for rows.Next() {
		var item domain.TaskEvent
		var created string
		if err := rows.Scan(&item.ID, &item.TaskID, &item.AttemptID, &item.Stream, &item.Message, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		events = append(events, item)
	}
	return events, rows.Err()
}

// GetTargetReport assembles all retained task and evidence records for a target.
func (s *Store) GetTargetReport(ctx context.Context, targetID string) (domain.TargetReport, error) {
	target, err := s.GetTarget(ctx, targetID)
	if err != nil {
		return domain.TargetReport{}, err
	}
	report := domain.TargetReport{
		Target:       target,
		Tasks:        []domain.Task{},
		Events:       []domain.TaskEvent{},
		Artifacts:    []domain.Artifact{},
		Transactions: []domain.HTTPExchange{},
		Observations: []domain.Observation{},
		Findings:     []domain.Finding{},
	}
	report.Tasks, err = s.listTargetTasks(ctx, targetID)
	if err != nil {
		return domain.TargetReport{}, err
	}
	for _, task := range report.Tasks {
		events, eventErr := s.ListTaskEvents(ctx, task.ID)
		if eventErr != nil {
			return domain.TargetReport{}, eventErr
		}
		report.Events = append(report.Events, events...)
	}
	if report.Artifacts, err = s.listArtifacts(ctx, targetID); err != nil {
		return domain.TargetReport{}, err
	}
	if report.Transactions, err = s.listExchanges(ctx, targetID); err != nil {
		return domain.TargetReport{}, err
	}
	if report.Observations, err = s.listObservations(ctx, targetID); err != nil {
		return domain.TargetReport{}, err
	}
	if report.Findings, err = s.listFindings(ctx, targetID); err != nil {
		return domain.TargetReport{}, err
	}
	return report, nil
}

func (s *Store) listTargetTasks(ctx context.Context, targetID string) ([]domain.Task, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT t.public_id, r.public_id, tg.public_id, t.plugin_id, t.status, t.error,
       t.created_at, t.started_at, t.ended_at
FROM tasks t JOIN runs r ON r.id=t.run_id JOIN targets tg ON tg.id=t.target_id
WHERE tg.public_id=? ORDER BY t.id DESC`, targetID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]domain.Task, 0)
	for rows.Next() {
		item, err := scanTask(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

func (s *Store) listArtifacts(ctx context.Context, targetID string) ([]domain.Artifact, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT a.public_id, t.public_id, a.name, a.media_type, a.size, a.sha256, a.path, a.created_at
FROM artifacts a JOIN tasks t ON t.id=a.task_id JOIN targets tg ON tg.id=t.target_id
WHERE tg.public_id=? ORDER BY a.id DESC`, targetID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]domain.Artifact, 0)
	for rows.Next() {
		var item domain.Artifact
		var created string
		if err := rows.Scan(&item.ID, &item.TaskID, &item.Name, &item.MediaType, &item.Size, &item.SHA256, &item.Path, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		items = append(items, item)
	}
	return items, rows.Err()
}

// GetArtifact returns artifact metadata by public ID.
func (s *Store) GetArtifact(ctx context.Context, artifactID string) (domain.Artifact, error) {
	var item domain.Artifact
	var created string
	err := s.db.QueryRowContext(ctx, `
SELECT a.public_id, t.public_id, a.name, a.media_type, a.size, a.sha256, a.path, a.created_at
FROM artifacts a JOIN tasks t ON t.id=a.task_id WHERE a.public_id=?`, artifactID).
		Scan(&item.ID, &item.TaskID, &item.Name, &item.MediaType, &item.Size, &item.SHA256, &item.Path, &created)
	if errors.Is(err, sql.ErrNoRows) {
		return domain.Artifact{}, ErrNotFound
	}
	if err != nil {
		return domain.Artifact{}, err
	}
	item.CreatedAt = parseTime(created)
	return item, nil
}

func (s *Store) listExchanges(ctx context.Context, targetID string) ([]domain.HTTPExchange, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT e.public_id, t.public_id, tg.public_id, e.method, e.url, e.request_headers, e.status_code,
       e.response_headers, COALESCE(a.public_id,''), e.duration_ms, e.created_at
FROM http_exchanges e JOIN tasks t ON t.id=e.task_id JOIN targets tg ON tg.id=e.target_id
LEFT JOIN artifacts a ON a.id=e.response_body_artifact_id
WHERE tg.public_id=? ORDER BY e.id DESC`, targetID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanExchanges(rows)
}

// ListHTTPExchanges returns captured transactions for a session and optional
// target, newest first.
func (s *Store) ListHTTPExchanges(ctx context.Context, sessionID, targetID string) ([]domain.HTTPExchange, error) {
	query := `
SELECT e.public_id, t.public_id, tg.public_id, e.method, e.url, e.request_headers, e.status_code,
       e.response_headers, COALESCE(ar.public_id,''), e.duration_ms, e.created_at
FROM http_exchanges e JOIN tasks t ON t.id=e.task_id JOIN targets tg ON tg.id=e.target_id
JOIN sessions s ON s.id=tg.session_id
LEFT JOIN artifacts ar ON ar.id=e.response_body_artifact_id
WHERE s.public_id=?`
	args := []any{sessionID}
	if targetID != "" {
		query += ` AND tg.public_id=?`
		args = append(args, targetID)
	}
	query += ` ORDER BY e.id DESC`
	rows, err := s.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanExchanges(rows)
}

func scanExchanges(rows *sql.Rows) ([]domain.HTTPExchange, error) {
	items := make([]domain.HTTPExchange, 0)
	for rows.Next() {
		var item domain.HTTPExchange
		var created string
		if err := rows.Scan(&item.ID, &item.TaskID, &item.TargetID, &item.Method, &item.URL,
			&item.RequestHeaders, &item.StatusCode, &item.ResponseHeaders, &item.ResponseBodyArtifactID,
			&item.DurationMS, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		items = append(items, item)
	}
	return items, rows.Err()
}

func (s *Store) listObservations(ctx context.Context, targetID string) ([]domain.Observation, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT o.public_id, t.public_id, tg.public_id, o.technique_code, o.kind, o.data, o.created_at
FROM observations o JOIN tasks t ON t.id=o.task_id JOIN targets tg ON tg.id=o.target_id
WHERE tg.public_id=? ORDER BY o.id DESC`, targetID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]domain.Observation, 0)
	for rows.Next() {
		var item domain.Observation
		var created string
		if err := rows.Scan(&item.ID, &item.TaskID, &item.TargetID, &item.TechniqueCode, &item.Kind, &item.Data, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		items = append(items, item)
	}
	return items, rows.Err()
}

func (s *Store) listFindings(ctx context.Context, targetID string) ([]domain.Finding, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT f.public_id, t.public_id, tg.public_id, f.technique_code, f.title, f.severity, f.description, f.created_at
FROM findings f JOIN tasks t ON t.id=f.task_id JOIN targets tg ON tg.id=f.target_id
WHERE tg.public_id=? ORDER BY f.id DESC`, targetID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]domain.Finding, 0)
	for rows.Next() {
		var item domain.Finding
		var created string
		if err := rows.Scan(&item.ID, &item.TaskID, &item.TargetID, &item.TechniqueCode, &item.Title,
			&item.Severity, &item.Description, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		items = append(items, item)
	}
	return items, rows.Err()
}

func newID(prefix string) string {
	var bytes [12]byte
	if _, err := rand.Read(bytes[:]); err != nil {
		panic("crypto/rand unavailable: " + err.Error())
	}
	return prefix + "_" + hex.EncodeToString(bytes[:])
}

// NewID creates an opaque public ID with a readable record-type prefix.
func NewID(prefix string) string { return newID(prefix) }

func formatTime(value time.Time) string { return value.UTC().Format(time.RFC3339Nano) }

func parseTime(value string) time.Time {
	parsed, _ := time.Parse(time.RFC3339Nano, value)
	return parsed
}

func parseNullTime(value sql.NullString) *time.Time {
	if !value.Valid {
		return nil
	}
	parsed := parseTime(value.String)
	return &parsed
}
