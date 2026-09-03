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
	"github.com/owtf/owtf/internal/model"
	targetvalue "github.com/owtf/owtf/internal/target"
)

const maxPluginOutputNotes = 64 << 10

var (
	// ErrNotFound indicates that a requested public ID does not exist.
	ErrNotFound = errors.New("not found")
	// ErrConflict indicates that current state prevents a destructive change.
	ErrConflict = errors.New("conflict")
	// ErrTaskNotRunning indicates that a terminal task cannot transition again.
	ErrTaskNotRunning = errors.New("task is not running")
	// ErrInvalid indicates that supplied state violates a store invariant.
	ErrInvalid = errors.New("invalid input")
)

// TaskSpec is one validated target/plugin pair used to create a durable task.
type TaskSpec struct {
	TargetID       string
	PluginID       string
	PluginVersion  string
	PluginSnapshot string
	Status         string
	Error          string
}

// Store is a serialized SQLite connection for OWTF state.
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
    scope INTEGER NOT NULL DEFAULT 1,
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
    plugin_group TEXT NOT NULL,
    plugin_type TEXT NOT NULL,
    techniques_json TEXT NOT NULL,
    inputs_json TEXT NOT NULL DEFAULT '[]',
    runtime_type TEXT NOT NULL,
    availability TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    profile TEXT NOT NULL DEFAULT '',
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
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    media_type TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    path TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    request_headers TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_headers TEXT NOT NULL,
    source_artifact_id INTEGER REFERENCES artifacts(id) ON DELETE SET NULL,
    request_body_artifact_id INTEGER REFERENCES artifacts(id) ON DELETE SET NULL,
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
);
CREATE TABLE IF NOT EXISTS plugin_output_reviews (
    task_id INTEGER PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
    rank TEXT NOT NULL CHECK(rank IN ('unranked', 'passing', 'informational', 'low', 'medium', 'high', 'critical')),
    notes TEXT NOT NULL,
    updated_at TEXT NOT NULL
);`
	if _, err := s.db.ExecContext(ctx, schema); err != nil {
		return fmt.Errorf("migrate database: %w", err)
	}
	if err := s.migratePluginColumns(ctx); err != nil {
		return err
	}
	if err := s.migrateTargetColumns(ctx); err != nil {
		return err
	}
	if err := s.migrateRunColumns(ctx); err != nil {
		return err
	}
	if err := s.migrateTransactionTables(ctx); err != nil {
		return err
	}
	if _, err := s.db.ExecContext(ctx, `DELETE FROM runs WHERE NOT EXISTS (SELECT 1 FROM tasks WHERE tasks.run_id=runs.id)`); err != nil {
		return fmt.Errorf("prune empty runs: %w", err)
	}
	return nil
}

func (s *Store) migrateTargetColumns(ctx context.Context) error {
	columns, err := s.tableColumns(ctx, "targets")
	if err != nil {
		return err
	}
	if columns["scope"] {
		return nil
	}
	if _, err := s.db.ExecContext(ctx, `ALTER TABLE targets ADD COLUMN scope INTEGER NOT NULL DEFAULT 1`); err != nil {
		return fmt.Errorf("add target scope column: %w", err)
	}
	return nil
}

func (s *Store) migrateRunColumns(ctx context.Context) error {
	columns, err := s.tableColumns(ctx, "runs")
	if err != nil {
		return err
	}
	if columns["profile"] {
		return nil
	}
	if _, err := s.db.ExecContext(ctx, `ALTER TABLE runs ADD COLUMN profile TEXT NOT NULL DEFAULT ''`); err != nil {
		return fmt.Errorf("add run profile column: %w", err)
	}
	return nil
}

// migrateTransactionTables makes transactions and their files target-owned.
// Older rewrite databases required a plugin task, which prevented importing
// proxy traffic directly as OWTF transactions.
func (s *Store) migrateTransactionTables(ctx context.Context) error {
	columns, err := s.tableColumns(ctx, "artifacts")
	if err != nil {
		return err
	}
	if !columns["target_id"] {
		if err := s.rebuildTransactionTables(ctx); err != nil {
			return err
		}
	}
	_, err = s.db.ExecContext(ctx, `
CREATE INDEX IF NOT EXISTS artifacts_target_idx ON artifacts(target_id, id);
CREATE INDEX IF NOT EXISTS transactions_target_idx ON transactions(target_id, id);`)
	if err != nil {
		return fmt.Errorf("index transaction tables: %w", err)
	}
	return nil
}

func (s *Store) tableColumns(ctx context.Context, table string) (map[string]bool, error) {
	rows, err := s.db.QueryContext(ctx, `PRAGMA table_info(`+table+`)`)
	if err != nil {
		return nil, fmt.Errorf("inspect %s schema: %w", table, err)
	}
	defer rows.Close()
	columns := make(map[string]bool)
	for rows.Next() {
		var index, notNull, primaryKey int
		var name, columnType string
		var defaultValue any
		if err := rows.Scan(&index, &name, &columnType, &notNull, &defaultValue, &primaryKey); err != nil {
			return nil, fmt.Errorf("inspect %s column: %w", table, err)
		}
		columns[name] = true
	}
	return columns, rows.Err()
}

func (s *Store) rebuildTransactionTables(ctx context.Context) (returnErr error) {
	connection, err := s.db.Conn(ctx)
	if err != nil {
		return err
	}
	defer connection.Close()
	if _, err := connection.ExecContext(ctx, `PRAGMA foreign_keys=OFF`); err != nil {
		return fmt.Errorf("disable foreign keys for transaction migration: %w", err)
	}
	defer func() {
		if _, err := connection.ExecContext(context.Background(), `PRAGMA foreign_keys=ON`); returnErr == nil && err != nil {
			returnErr = fmt.Errorf("restore foreign keys after transaction migration: %w", err)
		}
	}()

	tx, err := connection.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	statements := []string{
		`DROP TABLE IF EXISTS transactions`,
		`ALTER TABLE http_exchanges RENAME TO http_exchanges_legacy`,
		`ALTER TABLE artifacts RENAME TO artifacts_legacy`,
		`CREATE TABLE artifacts (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    media_type TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    path TEXT NOT NULL,
    created_at TEXT NOT NULL
)`,
		`CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    request_headers TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_headers TEXT NOT NULL,
    source_artifact_id INTEGER REFERENCES artifacts(id) ON DELETE SET NULL,
    request_body_artifact_id INTEGER REFERENCES artifacts(id) ON DELETE SET NULL,
    response_body_artifact_id INTEGER REFERENCES artifacts(id) ON DELETE SET NULL,
    duration_ms INTEGER NOT NULL,
    created_at TEXT NOT NULL
)`,
		`INSERT INTO artifacts(id, public_id, task_id, target_id, name, media_type, size, sha256, path, created_at)
SELECT a.id, a.public_id, a.task_id, t.target_id, a.name, a.media_type, a.size, a.sha256, a.path, a.created_at
FROM artifacts_legacy a JOIN tasks t ON t.id=a.task_id`,
		`INSERT INTO transactions(id, public_id, task_id, target_id, method, url, request_headers, status_code,
response_headers, source_artifact_id, request_body_artifact_id, response_body_artifact_id, duration_ms, created_at)
SELECT id, public_id, task_id, target_id, method, url, request_headers, status_code,
response_headers, NULL, NULL, response_body_artifact_id, duration_ms, created_at FROM http_exchanges_legacy`,
		`DROP TABLE http_exchanges_legacy`,
		`DROP TABLE artifacts_legacy`,
	}
	for _, statement := range statements {
		if _, err := tx.ExecContext(ctx, statement); err != nil {
			return fmt.Errorf("migrate transaction tables: %w", err)
		}
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit transaction migration: %w", err)
	}
	var violations sql.NullString
	if err := connection.QueryRowContext(ctx, `SELECT group_concat("table" || ':' || rowid) FROM pragma_foreign_key_check`).Scan(&violations); err != nil && !errors.Is(err, sql.ErrNoRows) {
		return fmt.Errorf("check migrated foreign keys: %w", err)
	}
	if violations.Valid {
		return fmt.Errorf("transaction migration left invalid foreign keys: %s", violations.String)
	}
	return nil
}

// migratePluginColumns upgrades databases created before OWTF restored the
// established plugin group and type names.
func (s *Store) migratePluginColumns(ctx context.Context) error {
	rows, err := s.db.QueryContext(ctx, `PRAGMA table_info(plugins)`)
	if err != nil {
		return fmt.Errorf("inspect plugin schema: %w", err)
	}
	columns := make(map[string]bool)
	for rows.Next() {
		var index, notNull, primaryKey int
		var name, columnType string
		var defaultValue any
		if err := rows.Scan(&index, &name, &columnType, &notNull, &defaultValue, &primaryKey); err != nil {
			rows.Close()
			return fmt.Errorf("inspect plugin column: %w", err)
		}
		columns[name] = true
	}
	if err := rows.Close(); err != nil {
		return err
	}
	if columns["variant"] && !columns["plugin_type"] {
		if _, err := s.db.ExecContext(ctx, `ALTER TABLE plugins RENAME COLUMN variant TO plugin_type`); err != nil {
			return fmt.Errorf("rename plugin type column: %w", err)
		}
		columns["plugin_type"] = true
	}
	if !columns["plugin_type"] {
		return errors.New("plugins table is missing plugin_type")
	}
	if !columns["plugin_group"] {
		if _, err := s.db.ExecContext(ctx, `ALTER TABLE plugins ADD COLUMN plugin_group TEXT NOT NULL DEFAULT 'web'`); err != nil {
			return fmt.Errorf("add plugin group column: %w", err)
		}
	}
	if !columns["inputs_json"] {
		if _, err := s.db.ExecContext(ctx, `ALTER TABLE plugins ADD COLUMN inputs_json TEXT NOT NULL DEFAULT '[]'`); err != nil {
			return fmt.Errorf("add plugin inputs column: %w", err)
		}
	}
	return nil
}

// CreateSession creates a named scan workspace.
func (s *Store) CreateSession(ctx context.Context, name string) (model.Session, error) {
	name = strings.TrimSpace(name)
	if name == "" {
		name = "Default session"
	}
	session := model.Session{ID: newID("ses"), Name: name, CreatedAt: time.Now().UTC()}
	_, err := s.db.ExecContext(ctx, `INSERT INTO sessions(public_id, name, created_at) VALUES(?, ?, ?)`,
		session.ID, session.Name, formatTime(session.CreatedAt))
	if err != nil {
		return model.Session{}, fmt.Errorf("create session: %w", err)
	}
	return session, nil
}

// ListSessions returns sessions newest first.
func (s *Store) ListSessions(ctx context.Context) ([]model.Session, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT public_id, name, created_at FROM sessions ORDER BY id DESC`)
	if err != nil {
		return nil, fmt.Errorf("list sessions: %w", err)
	}
	defer rows.Close()
	sessions := make([]model.Session, 0)
	for rows.Next() {
		var item model.Session
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
func (s *Store) GetSession(ctx context.Context, id string) (model.Session, error) {
	var item model.Session
	var created string
	err := s.db.QueryRowContext(ctx, `SELECT public_id, name, created_at FROM sessions WHERE public_id = ?`, id).
		Scan(&item.ID, &item.Name, &created)
	if errors.Is(err, sql.ErrNoRows) {
		return model.Session{}, ErrNotFound
	}
	if err != nil {
		return model.Session{}, err
	}
	item.CreatedAt = parseTime(created)
	return item, nil
}

// DeleteSession removes a session and all of its target and execution records.
// Active work must be cancelled before the session can be deleted.
func (s *Store) DeleteSession(ctx context.Context, id string) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var sessionPK int64
	if err := tx.QueryRowContext(ctx, `SELECT id FROM sessions WHERE public_id=?`, id).Scan(&sessionPK); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return ErrNotFound
		}
		return err
	}
	var active int
	if err := tx.QueryRowContext(ctx, `
SELECT COUNT(*) FROM tasks t JOIN runs r ON r.id=t.run_id
WHERE r.session_id=? AND t.status IN (?, ?)`, sessionPK, model.TaskQueued, model.TaskRunning).Scan(&active); err != nil {
		return err
	}
	if active != 0 {
		return fmt.Errorf("%w: session has active work", ErrConflict)
	}
	if _, err := tx.ExecContext(ctx, `DELETE FROM sessions WHERE id=?`, sessionPK); err != nil {
		return err
	}
	return tx.Commit()
}

// AddTargetsResult separates newly stored targets from normalized duplicates.
type AddTargetsResult struct {
	Created    []model.Target `json:"created"`
	Duplicates []string       `json:"duplicates"`
}

// TargetFilter is a bounded target search within one session.
type TargetFilter struct {
	Search string
	Kind   string
	Scope  *bool
	Limit  int
	Offset int
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
	result := AddTargetsResult{Created: []model.Target{}, Duplicates: []string{}}
	now := time.Now().UTC()
	for _, normalized := range targets {
		item := model.Target{
			ID: newID("tgt"), SessionID: sessionID, Kind: normalized.Kind,
			Original: normalized.Original, Value: normalized.Value, Scope: true, CreatedAt: now,
		}
		_, err := s.db.ExecContext(ctx, `
INSERT INTO targets(public_id, session_id, kind, original, value, scope, created_at)
VALUES(?, ?, ?, ?, ?, ?, ?)`, item.ID, sessionPK, item.Kind, item.Original, item.Value, item.Scope, formatTime(item.CreatedAt))
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
func (s *Store) ListTargets(ctx context.Context, sessionID string) ([]model.Target, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT t.public_id, s.public_id, t.kind, t.original, t.value, t.scope, t.created_at
FROM targets t JOIN sessions s ON s.id = t.session_id
WHERE s.public_id = ? ORDER BY t.id DESC`, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	targets := make([]model.Target, 0)
	for rows.Next() {
		item, err := scanTarget(rows)
		if err != nil {
			return nil, err
		}
		targets = append(targets, item)
	}
	return targets, rows.Err()
}

// SearchTargets returns a deterministic page and both unfiltered and filtered
// counts. Limit must be between 1 and 1000.
func (s *Store) SearchTargets(ctx context.Context, sessionID string, filter TargetFilter) (model.TargetSearchResult, error) {
	if filter.Limit < 1 || filter.Limit > 1000 || filter.Offset < 0 {
		return model.TargetSearchResult{}, errors.New("invalid target search bounds")
	}
	if _, err := s.GetSession(ctx, sessionID); err != nil {
		return model.TargetSearchResult{}, err
	}
	result := model.TargetSearchResult{Data: []model.Target{}}
	if err := s.db.QueryRowContext(ctx, `
SELECT COUNT(*) FROM targets t JOIN sessions s ON s.id=t.session_id WHERE s.public_id=?`, sessionID).
		Scan(&result.RecordsTotal); err != nil {
		return model.TargetSearchResult{}, err
	}
	where := []string{"s.public_id=?"}
	args := []any{sessionID}
	if filter.Search != "" {
		where = append(where, `(LOWER(t.value) LIKE '%' || LOWER(?) || '%' OR LOWER(t.original) LIKE '%' || LOWER(?) || '%')`)
		args = append(args, filter.Search, filter.Search)
	}
	if filter.Kind != "" {
		where = append(where, "t.kind=?")
		args = append(args, filter.Kind)
	}
	if filter.Scope != nil {
		where = append(where, "t.scope=?")
		args = append(args, *filter.Scope)
	}
	predicate := strings.Join(where, " AND ")
	if err := s.db.QueryRowContext(ctx, `
SELECT COUNT(*) FROM targets t JOIN sessions s ON s.id=t.session_id WHERE `+predicate, args...).
		Scan(&result.RecordsFiltered); err != nil {
		return model.TargetSearchResult{}, err
	}
	queryArgs := append(append([]any(nil), args...), filter.Limit, filter.Offset)
	rows, err := s.db.QueryContext(ctx, `
SELECT t.public_id, s.public_id, t.kind, t.original, t.value, t.scope, t.created_at
FROM targets t JOIN sessions s ON s.id=t.session_id
WHERE `+predicate+` ORDER BY t.id DESC LIMIT ? OFFSET ?`, queryArgs...)
	if err != nil {
		return model.TargetSearchResult{}, err
	}
	defer rows.Close()
	for rows.Next() {
		item, err := scanTarget(rows)
		if err != nil {
			return model.TargetSearchResult{}, err
		}
		result.Data = append(result.Data, item)
	}
	return result, rows.Err()
}

// GetTarget returns one target by public ID.
func (s *Store) GetTarget(ctx context.Context, id string) (model.Target, error) {
	row := s.db.QueryRowContext(ctx, `
SELECT t.public_id, s.public_id, t.kind, t.original, t.value, t.scope, t.created_at
FROM targets t JOIN sessions s ON s.id = t.session_id WHERE t.public_id = ?`, id)
	item, err := scanTarget(row)
	if errors.Is(err, sql.ErrNoRows) {
		return model.Target{}, ErrNotFound
	}
	return item, err
}

// UpdateTargetScope changes whether a target participates in scoped work.
func (s *Store) UpdateTargetScope(ctx context.Context, id string, scope bool) (model.Target, error) {
	result, err := s.db.ExecContext(ctx, `UPDATE targets SET scope=? WHERE public_id=?`, scope, id)
	if err != nil {
		return model.Target{}, err
	}
	if count, _ := result.RowsAffected(); count == 0 {
		return model.Target{}, ErrNotFound
	}
	return s.GetTarget(ctx, id)
}

// DeleteTarget removes a target and its dependent execution evidence.
func (s *Store) DeleteTarget(ctx context.Context, id string) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var targetPK int64
	if err := tx.QueryRowContext(ctx, `SELECT id FROM targets WHERE public_id=?`, id).Scan(&targetPK); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return ErrNotFound
		}
		return err
	}
	var active int
	if err := tx.QueryRowContext(ctx, `
SELECT COUNT(*) FROM tasks WHERE target_id=? AND status IN (?, ?)`, targetPK, model.TaskQueued, model.TaskRunning).
		Scan(&active); err != nil {
		return err
	}
	if active != 0 {
		return fmt.Errorf("%w: target has active work", ErrConflict)
	}
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

func scanTarget(row rowScanner) (model.Target, error) {
	var item model.Target
	var created string
	err := row.Scan(&item.ID, &item.SessionID, &item.Kind, &item.Original, &item.Value, &item.Scope, &created)
	if err == nil {
		item.CreatedAt = parseTime(created)
	}
	return item, err
}

// ReplacePlugins atomically synchronizes the indexed plugin catalog.
func (s *Store) ReplacePlugins(ctx context.Context, plugins []model.Plugin) error {
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
		techniquesJSON, err := json.Marshal(item.Techniques)
		if err != nil {
			return fmt.Errorf("encode plugin %s techniques: %w", item.ID, err)
		}
		inputsJSON, err := json.Marshal(item.Inputs)
		if err != nil {
			return fmt.Errorf("encode plugin %s inputs: %w", item.ID, err)
		}
		updated := time.Now().UTC()
		_, err = tx.ExecContext(ctx, `
INSERT INTO plugins(id, version, title, description, plugin_group, plugin_type, techniques_json, inputs_json, runtime_type, availability, reason, updated_at)
VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, item.ID, item.Version, item.Title, item.Description, item.Group, item.Type,
			string(techniquesJSON), string(inputsJSON), item.RuntimeType, item.Availability, item.Reason, formatTime(updated))
		if err != nil {
			return err
		}
		for _, technique := range item.Techniques {
			if _, err := tx.ExecContext(ctx, `INSERT INTO techniques(code, title) VALUES(?, ?)
ON CONFLICT(code) DO UPDATE SET title=excluded.title`, technique.Code, technique.Title); err != nil {
				return err
			}
		}
	}
	return tx.Commit()
}

// ListPlugins returns the current indexed catalog ordered by plugin ID.
func (s *Store) ListPlugins(ctx context.Context) ([]model.Plugin, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT id, version, title, description, plugin_group, plugin_type, techniques_json, inputs_json, runtime_type, availability, reason, updated_at
FROM plugins ORDER BY id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	plugins := make([]model.Plugin, 0)
	for rows.Next() {
		var item model.Plugin
		var techniquesJSON, inputsJSON, updated string
		if err := rows.Scan(&item.ID, &item.Version, &item.Title, &item.Description, &item.Group, &item.Type,
			&techniquesJSON, &inputsJSON, &item.RuntimeType, &item.Availability, &item.Reason, &updated); err != nil {
			return nil, err
		}
		if err := json.Unmarshal([]byte(techniquesJSON), &item.Techniques); err != nil {
			return nil, fmt.Errorf("decode plugin %s techniques: %w", item.ID, err)
		}
		normalizeStoredTechniques(item.Title, item.Techniques)
		if err := json.Unmarshal([]byte(inputsJSON), &item.Inputs); err != nil {
			return nil, fmt.Errorf("decode plugin %s inputs: %w", item.ID, err)
		}
		item.UpdatedAt = parseTime(updated)
		plugins = append(plugins, item)
	}
	return plugins, rows.Err()
}

// CreateRun atomically creates an immutable launch record and its tasks.
func (s *Store) CreateRun(ctx context.Context, sessionID, profile string, specs []TaskSpec) (model.Run, []model.Task, error) {
	if len(specs) == 0 {
		return model.Run{}, nil, fmt.Errorf("at least one task is required")
	}
	hasQueued := false
	for index := range specs {
		if specs[index].Status == "" {
			specs[index].Status = model.TaskQueued
		}
		switch specs[index].Status {
		case model.TaskQueued:
			hasQueued = true
		case model.TaskBlocked:
			if strings.TrimSpace(specs[index].Error) == "" {
				return model.Run{}, nil, errors.New("blocked task requires an error")
			}
		default:
			return model.Run{}, nil, fmt.Errorf("invalid initial task status %q", specs[index].Status)
		}
	}
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return model.Run{}, nil, err
	}
	defer tx.Rollback()
	var sessionPK int64
	if err := tx.QueryRowContext(ctx, `SELECT id FROM sessions WHERE public_id = ?`, sessionID).Scan(&sessionPK); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return model.Run{}, nil, ErrNotFound
		}
		return model.Run{}, nil, err
	}
	now := time.Now().UTC()
	run := model.Run{
		ID: newID("run"), SessionID: sessionID, Profile: strings.TrimSpace(profile),
		Status: model.RunQueued, CreatedAt: now,
	}
	if !hasQueued {
		run.Status = model.RunBlocked
		run.FinishedAt = &now
	}
	result, err := tx.ExecContext(ctx, `INSERT INTO runs(public_id, session_id, profile, status, created_at, finished_at) VALUES(?, ?, ?, ?, ?, ?)`,
		run.ID, sessionPK, run.Profile, run.Status, formatTime(run.CreatedAt), nullableTime(run.FinishedAt))
	if err != nil {
		return model.Run{}, nil, err
	}
	runPK, _ := result.LastInsertId()
	tasks := make([]model.Task, 0, len(specs))
	for _, spec := range specs {
		var targetPK int64
		if err := tx.QueryRowContext(ctx, `SELECT id FROM targets WHERE public_id = ? AND session_id = ?`, spec.TargetID, sessionPK).Scan(&targetPK); err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				return model.Run{}, nil, fmt.Errorf("target %s does not belong to session", spec.TargetID)
			}
			return model.Run{}, nil, err
		}
		task := model.Task{
			ID: newID("tsk"), RunID: run.ID, TargetID: spec.TargetID, PluginID: spec.PluginID,
			Status: spec.Status, Error: spec.Error, CreatedAt: now,
		}
		task.Inputs, task.Techniques, err = taskSnapshotDetails(spec.PluginSnapshot)
		if err != nil {
			return model.Run{}, nil, fmt.Errorf("decode plugin %s snapshot: %w", spec.PluginID, err)
		}
		if task.Status == model.TaskBlocked {
			task.EndedAt = &now
		}
		_, err := tx.ExecContext(ctx, `
INSERT INTO tasks(public_id, run_id, target_id, plugin_id, plugin_version, plugin_snapshot, status, error, created_at, ended_at)
VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, task.ID, runPK, targetPK, spec.PluginID, spec.PluginVersion,
			spec.PluginSnapshot, task.Status, task.Error, formatTime(task.CreatedAt), nullableTime(task.EndedAt))
		if err != nil {
			return model.Run{}, nil, err
		}
		if task.Status == model.TaskBlocked {
			if _, err := tx.ExecContext(ctx, `
INSERT INTO task_events(task_id, stream, message, created_at)
VALUES((SELECT id FROM tasks WHERE public_id=?), 'lifecycle', ?, ?)`, task.ID, "task blocked: "+task.Error, formatTime(now)); err != nil {
				return model.Run{}, nil, err
			}
		}
		tasks = append(tasks, task)
	}
	if err := tx.Commit(); err != nil {
		return model.Run{}, nil, err
	}
	return run, tasks, nil
}

// ListRuns returns all runs in a session, newest first.
func (s *Store) ListRuns(ctx context.Context, sessionID string) ([]model.Run, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT r.public_id, s.public_id, r.profile, r.status, r.created_at, r.started_at, r.finished_at
FROM runs r JOIN sessions s ON s.id=r.session_id
WHERE s.public_id=? ORDER BY r.id DESC`, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	runs := make([]model.Run, 0)
	for rows.Next() {
		item, err := scanRun(rows)
		if err != nil {
			return nil, err
		}
		runs = append(runs, item)
	}
	return runs, rows.Err()
}

// GetRun returns one run by public ID.
func (s *Store) GetRun(ctx context.Context, runID string) (model.Run, error) {
	row := s.db.QueryRowContext(ctx, `
SELECT r.public_id, s.public_id, r.profile, r.status, r.created_at, r.started_at, r.finished_at
FROM runs r JOIN sessions s ON s.id=r.session_id WHERE r.public_id=?`, runID)
	item, err := scanRun(row)
	if errors.Is(err, sql.ErrNoRows) {
		return model.Run{}, ErrNotFound
	}
	return item, err
}

func scanRun(row rowScanner) (model.Run, error) {
	var item model.Run
	var created string
	var started, finished sql.NullString
	err := row.Scan(&item.ID, &item.SessionID, &item.Profile, &item.Status, &created, &started, &finished)
	item.CreatedAt = parseTime(created)
	item.StartedAt = parseNullTime(started)
	item.FinishedAt = parseNullTime(finished)
	return item, err
}

// RecoverTasks marks interrupted attempts failed and returns their task IDs for
// a new queued attempt.
func (s *Store) RecoverTasks(ctx context.Context) ([]string, error) {
	now := formatTime(time.Now().UTC())
	if _, err := s.db.ExecContext(ctx, `
UPDATE attempts SET status = ?, ended_at = ?, error = 'server restarted during execution'
WHERE status = ?`, model.TaskFailed, now, model.TaskRunning); err != nil {
		return nil, err
	}
	if _, err := s.db.ExecContext(ctx, `
UPDATE tasks SET status = ?, error = 'recovered after server restart', started_at = NULL
WHERE status = ?`, model.TaskQueued, model.TaskRunning); err != nil {
		return nil, err
	}
	rows, err := s.db.QueryContext(ctx, `SELECT public_id FROM tasks WHERE status = ? ORDER BY id`, model.TaskQueued)
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
func (s *Store) StartTask(ctx context.Context, taskID string) (model.TaskExecution, error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return model.TaskExecution{}, err
	}
	defer tx.Rollback()
	var taskPK, runPK, targetPK int64
	var execution model.TaskExecution
	var targetCreated, taskCreated string
	err = tx.QueryRowContext(ctx, `
SELECT t.id, t.public_id, r.id, r.public_id, tg.id, tg.public_id, a.public_id,
       tg.kind, tg.original, tg.value, tg.scope, tg.created_at, t.plugin_id,
       t.plugin_snapshot, t.status, t.created_at
FROM tasks t
JOIN runs r ON r.id = t.run_id
JOIN targets tg ON tg.id = t.target_id
JOIN sessions a ON a.id = tg.session_id
WHERE t.public_id = ?`, taskID).Scan(
		&taskPK, &execution.ID, &runPK, &execution.RunID, &targetPK, &execution.Target.ID,
		&execution.Target.SessionID, &execution.Target.Kind, &execution.Target.Original,
		&execution.Target.Value, &execution.Target.Scope, &targetCreated, &execution.PluginID,
		&execution.PluginSnapshot, &execution.Status, &taskCreated,
	)
	if errors.Is(err, sql.ErrNoRows) {
		return model.TaskExecution{}, ErrNotFound
	}
	if err != nil {
		return model.TaskExecution{}, err
	}
	if execution.Status != model.TaskQueued {
		return model.TaskExecution{}, fmt.Errorf("%w: task is %s", ErrTaskNotRunning, execution.Status)
	}
	now := time.Now().UTC()
	execution.Target.CreatedAt = parseTime(targetCreated)
	execution.CreatedAt = parseTime(taskCreated)
	execution.TargetID = execution.Target.ID
	execution.Status = model.TaskRunning
	execution.StartedAt = &now
	var attemptNumber int
	if err := tx.QueryRowContext(ctx, `SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM attempts WHERE task_id = ?`, taskPK).Scan(&attemptNumber); err != nil {
		return model.TaskExecution{}, err
	}
	execution.AttemptID = newID("att")
	execution.AttemptNumber = attemptNumber
	if _, err := tx.ExecContext(ctx, `UPDATE tasks SET status = ?, error = '', started_at = ?, ended_at = NULL WHERE id = ?`,
		model.TaskRunning, formatTime(now), taskPK); err != nil {
		return model.TaskExecution{}, err
	}
	if _, err := tx.ExecContext(ctx, `INSERT INTO attempts(public_id, task_id, attempt_number, status, started_at) VALUES(?, ?, ?, ?, ?)`,
		execution.AttemptID, taskPK, attemptNumber, model.TaskRunning, formatTime(now)); err != nil {
		return model.TaskExecution{}, err
	}
	if _, err := tx.ExecContext(ctx, `UPDATE runs SET status = ?, started_at = COALESCE(started_at, ?) WHERE id = ?`,
		model.RunRunning, formatTime(now), runPK); err != nil {
		return model.TaskExecution{}, err
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
func (s *Store) CompleteTask(ctx context.Context, execution model.TaskExecution, artifacts []model.Artifact,
	transactions []model.Transaction, observations []model.Observation, findings []model.Finding) error {
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
	if taskStatus != model.TaskRunning {
		return ErrTaskNotRunning
	}
	artifactPKs := make(map[string]int64)
	for _, item := range artifacts {
		result, err := tx.ExecContext(ctx, `
		INSERT INTO artifacts(public_id, task_id, target_id, name, media_type, size, sha256, path, created_at)
	VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)`, item.ID, taskPK, targetPK, item.Name, item.MediaType, item.Size, item.SHA256,
			item.Path, formatTime(item.CreatedAt))
		if err != nil {
			return err
		}
		artifactPKs[item.ID], _ = result.LastInsertId()
	}
	for _, item := range transactions {
		var artifactPK any
		if item.ResponseBodyArtifactID != "" {
			artifactPK = artifactPKs[item.ResponseBodyArtifactID]
		}
		_, err := tx.ExecContext(ctx, `
			INSERT INTO transactions(public_id, task_id, target_id, method, url, request_headers, status_code,
		response_headers, source_artifact_id, request_body_artifact_id, response_body_artifact_id, duration_ms, created_at)
		VALUES(?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)`, item.ID, taskPK, targetPK, item.Method, item.URL,
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
	if _, err := tx.ExecContext(ctx, `UPDATE attempts SET status=?, ended_at=? WHERE id=?`, model.TaskSucceeded, formatTime(now), attemptPK); err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `UPDATE tasks SET status=?, ended_at=? WHERE id=?`, model.TaskSucceeded, formatTime(now), taskPK); err != nil {
		return err
	}
	if err := refreshRunStatus(ctx, tx, runPK, now); err != nil {
		return err
	}
	return tx.Commit()
}

// ImportTransactions atomically attaches proxy transactions and their retained
// files to an existing target. It intentionally creates no run or worklist task.
func (s *Store) ImportTransactions(ctx context.Context, targetID string, artifacts []model.Artifact, transactions []model.Transaction) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var targetPK int64
	if err := tx.QueryRowContext(ctx, `SELECT id FROM targets WHERE public_id=?`, targetID).Scan(&targetPK); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return ErrNotFound
		}
		return err
	}
	artifactPKs := make(map[string]int64, len(artifacts))
	for _, item := range artifacts {
		if item.ID == "" || item.TaskID != "" || (item.TargetID != "" && item.TargetID != targetID) {
			return errors.New("invalid imported artifact ownership")
		}
		result, err := tx.ExecContext(ctx, `
INSERT INTO artifacts(public_id, task_id, target_id, name, media_type, size, sha256, path, created_at)
VALUES(?, NULL, ?, ?, ?, ?, ?, ?, ?)`, item.ID, targetPK, item.Name, item.MediaType, item.Size,
			item.SHA256, item.Path, formatTime(item.CreatedAt))
		if err != nil {
			return fmt.Errorf("import artifact %s: %w", item.ID, err)
		}
		artifactPKs[item.ID], _ = result.LastInsertId()
	}
	for _, item := range transactions {
		if item.ID == "" || item.TaskID != "" || (item.TargetID != "" && item.TargetID != targetID) {
			return errors.New("invalid imported transaction ownership")
		}
		sourcePK, err := importedArtifactPK(artifactPKs, item.SourceArtifactID)
		if err != nil {
			return err
		}
		requestBodyPK, err := importedArtifactPK(artifactPKs, item.RequestBodyArtifactID)
		if err != nil {
			return err
		}
		bodyPK, err := importedArtifactPK(artifactPKs, item.ResponseBodyArtifactID)
		if err != nil {
			return err
		}
		_, err = tx.ExecContext(ctx, `
INSERT INTO transactions(public_id, task_id, target_id, method, url, request_headers, status_code,
response_headers, source_artifact_id, request_body_artifact_id, response_body_artifact_id, duration_ms, created_at)
VALUES(?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, item.ID, targetPK, item.Method, item.URL,
			item.RequestHeaders, item.StatusCode, item.ResponseHeaders, sourcePK, requestBodyPK, bodyPK, item.DurationMS,
			formatTime(item.CreatedAt))
		if err != nil {
			return fmt.Errorf("import transaction %s: %w", item.ID, err)
		}
	}
	return tx.Commit()
}

func importedArtifactPK(artifacts map[string]int64, id string) (any, error) {
	if id == "" {
		return nil, nil
	}
	primaryKey, ok := artifacts[id]
	if !ok {
		return nil, fmt.Errorf("import references unknown artifact %s", id)
	}
	return primaryKey, nil
}

// FailTask records a terminal execution error and refreshes its parent run.
func (s *Store) FailTask(ctx context.Context, execution model.TaskExecution, taskError error) error {
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
	if taskStatus != model.TaskRunning {
		return ErrTaskNotRunning
	}
	now := time.Now().UTC()
	message := taskError.Error()
	if _, err := tx.ExecContext(ctx, `UPDATE attempts SET status=?, ended_at=?, error=? WHERE id=?`, model.TaskFailed, formatTime(now), message, attemptPK); err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `UPDATE tasks SET status=?, ended_at=?, error=? WHERE id=?`, model.TaskFailed, formatTime(now), message, taskPK); err != nil {
		return err
	}
	if err := refreshRunStatus(ctx, tx, runPK, now); err != nil {
		return err
	}
	return tx.Commit()
}

func refreshRunStatus(ctx context.Context, tx *sql.Tx, runPK int64, now time.Time) error {
	var pending, failed, cancelled, blocked int
	if err := tx.QueryRowContext(ctx, `
SELECT SUM(CASE WHEN status IN ('queued','running') THEN 1 ELSE 0 END),
       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END),
       SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END),
       SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END)
FROM tasks WHERE run_id = ?`, runPK).Scan(&pending, &failed, &cancelled, &blocked); err != nil {
		return err
	}
	if pending != 0 {
		return nil
	}
	status := model.RunSucceeded
	if failed > 0 {
		status = model.RunFailed
	} else if cancelled > 0 {
		status = model.RunCancelled
	} else if blocked > 0 {
		status = model.RunBlocked
	}
	_, err := tx.ExecContext(ctx, `UPDATE runs SET status=?, finished_at=? WHERE id=?`, status, formatTime(now), runPK)
	return err
}

// ListTasks returns worklist tasks, optionally filtered by session and status.
func (s *Store) ListTasks(ctx context.Context, sessionID, status string) ([]model.Task, error) {
	query := `
SELECT t.public_id, r.public_id, tg.public_id, t.plugin_id, t.status, t.error,
       t.plugin_snapshot, t.created_at, t.started_at, t.ended_at
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
	tasks := make([]model.Task, 0)
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
func (s *Store) GetTask(ctx context.Context, taskID string) (model.Task, error) {
	row := s.db.QueryRowContext(ctx, `
SELECT t.public_id, r.public_id, tg.public_id, t.plugin_id, t.status, t.error,
       t.plugin_snapshot, t.created_at, t.started_at, t.ended_at
FROM tasks t JOIN runs r ON r.id=t.run_id JOIN targets tg ON tg.id=t.target_id
WHERE t.public_id=?`, taskID)
	item, err := scanTask(row)
	if errors.Is(err, sql.ErrNoRows) {
		return model.Task{}, ErrNotFound
	}
	return item, err
}

// CancelTask records operator cancellation for queued or running work.
func (s *Store) CancelTask(ctx context.Context, taskID string) (model.Task, error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return model.Task{}, err
	}
	defer tx.Rollback()
	var taskPK, runPK int64
	var status string
	if err := tx.QueryRowContext(ctx, `SELECT id, run_id, status FROM tasks WHERE public_id=?`, taskID).
		Scan(&taskPK, &runPK, &status); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return model.Task{}, ErrNotFound
		}
		return model.Task{}, err
	}
	if status == model.TaskQueued || status == model.TaskRunning {
		now := time.Now().UTC()
		if _, err := tx.ExecContext(ctx, `
UPDATE tasks SET status=?, error='cancelled by operator', ended_at=? WHERE id=?`,
			model.TaskCancelled, formatTime(now), taskPK); err != nil {
			return model.Task{}, err
		}
		if _, err := tx.ExecContext(ctx, `
UPDATE attempts SET status=?, error='cancelled by operator', ended_at=?
WHERE task_id=? AND status=?`, model.TaskCancelled, formatTime(now), taskPK, model.TaskRunning); err != nil {
			return model.Task{}, err
		}
		if err := refreshRunStatus(ctx, tx, runPK, now); err != nil {
			return model.Task{}, err
		}
	}
	if err := tx.Commit(); err != nil {
		return model.Task{}, err
	}
	return s.GetTask(ctx, taskID)
}

func scanTask(row rowScanner) (model.Task, error) {
	var item model.Task
	var snapshot, created string
	var started, ended sql.NullString
	err := row.Scan(&item.ID, &item.RunID, &item.TargetID, &item.PluginID, &item.Status, &item.Error,
		&snapshot, &created, &started, &ended)
	if err != nil {
		return model.Task{}, err
	}
	item.Inputs, item.Techniques, err = taskSnapshotDetails(snapshot)
	if err != nil {
		return model.Task{}, fmt.Errorf("decode task %s snapshot: %w", item.ID, err)
	}
	item.CreatedAt = parseTime(created)
	item.StartedAt = parseNullTime(started)
	item.EndedAt = parseNullTime(ended)
	return item, err
}

func taskSnapshotDetails(snapshot string) (map[string]any, []model.Technique, error) {
	var stored struct {
		Version  int `json:"version"`
		Manifest struct {
			Metadata struct {
				Title string `json:"title"`
			} `json:"metadata"`
			Spec struct {
				Techniques []model.Technique `json:"techniques"`
			} `json:"spec"`
		} `json:"manifest"`
		Metadata struct {
			Title string `json:"title"`
		} `json:"metadata"`
		Spec struct {
			Techniques []model.Technique `json:"techniques"`
		} `json:"spec"`
		Inputs map[string]any `json:"inputs"`
	}
	decoder := json.NewDecoder(strings.NewReader(snapshot))
	decoder.UseNumber()
	if err := decoder.Decode(&stored); err != nil {
		return nil, nil, err
	}
	if stored.Inputs == nil {
		stored.Inputs = make(map[string]any)
	}
	techniques := stored.Manifest.Spec.Techniques
	title := stored.Manifest.Metadata.Title
	if stored.Version == 0 {
		techniques = stored.Spec.Techniques
		title = stored.Metadata.Title
	}
	if techniques == nil {
		techniques = make([]model.Technique, 0)
	}
	normalizeStoredTechniques(title, techniques)
	return stored.Inputs, techniques, nil
}

func normalizeStoredTechniques(title string, techniques []model.Technique) {
	for index := range techniques {
		if techniques[index].Title == "" {
			techniques[index].Title = title
		}
		if techniques[index].Priority == 0 {
			techniques[index].Priority = 99
		}
	}
}

// ListTaskAttempts returns execution attempts in the order they started.
func (s *Store) ListTaskAttempts(ctx context.Context, taskID string) ([]model.TaskAttempt, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT a.public_id, t.public_id, a.attempt_number, a.status, a.started_at, a.ended_at, a.error
FROM attempts a JOIN tasks t ON t.id=a.task_id
WHERE t.public_id=? ORDER BY a.attempt_number`, taskID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanTaskAttempts(rows)
}

func scanTaskAttempts(rows *sql.Rows) ([]model.TaskAttempt, error) {
	attempts := make([]model.TaskAttempt, 0)
	for rows.Next() {
		var attempt model.TaskAttempt
		var started string
		var ended sql.NullString
		if err := rows.Scan(&attempt.ID, &attempt.TaskID, &attempt.AttemptNumber, &attempt.Status, &started, &ended, &attempt.Error); err != nil {
			return nil, err
		}
		attempt.StartedAt = parseTime(started)
		attempt.EndedAt = parseNullTime(ended)
		attempts = append(attempts, attempt)
	}
	return attempts, rows.Err()
}

// ListTaskEvents returns task output in insertion order.
func (s *Store) ListTaskEvents(ctx context.Context, taskID string) ([]model.TaskEvent, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT e.id, t.public_id, COALESCE(a.public_id,''), e.stream, e.message, e.created_at
FROM task_events e JOIN tasks t ON t.id=e.task_id LEFT JOIN attempts a ON a.id=e.attempt_id
WHERE t.public_id=? ORDER BY e.id`, taskID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	events := make([]model.TaskEvent, 0)
	for rows.Next() {
		var item model.TaskEvent
		var created string
		if err := rows.Scan(&item.ID, &item.TaskID, &item.AttemptID, &item.Stream, &item.Message, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		events = append(events, item)
	}
	return events, rows.Err()
}

// GetPluginOutputReview returns the rank and notes attached to one task output.
// Tasks without an explicit review are returned as unranked.
func (s *Store) GetPluginOutputReview(ctx context.Context, taskID string) (model.PluginOutputReview, error) {
	row := s.db.QueryRowContext(ctx, `
SELECT t.public_id, COALESCE(r.rank, ?), COALESCE(r.notes, ''), r.updated_at
FROM tasks t LEFT JOIN plugin_output_reviews r ON r.task_id=t.id
WHERE t.public_id=?`, model.PluginOutputRankUnranked, taskID)
	review, err := scanPluginOutputReview(row)
	if errors.Is(err, sql.ErrNoRows) {
		return model.PluginOutputReview{}, ErrNotFound
	}
	return review, err
}

// UpdatePluginOutputReview changes only operator-owned review state. Scanner
// evidence and task history remain immutable.
func (s *Store) UpdatePluginOutputReview(ctx context.Context, taskID string, rank, notes *string) (model.PluginOutputReview, error) {
	if rank == nil && notes == nil {
		return model.PluginOutputReview{}, fmt.Errorf("%w: rank or notes is required", ErrInvalid)
	}
	if rank != nil {
		value := strings.TrimSpace(*rank)
		if !validPluginOutputRank(value) {
			return model.PluginOutputReview{}, fmt.Errorf("%w: unsupported plugin output rank %q", ErrInvalid, value)
		}
		rank = &value
	}
	if notes != nil && len(*notes) > maxPluginOutputNotes {
		return model.PluginOutputReview{}, fmt.Errorf("%w: plugin output notes exceed %d bytes", ErrInvalid, maxPluginOutputNotes)
	}

	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return model.PluginOutputReview{}, err
	}
	defer tx.Rollback()
	var taskPK int64
	var status string
	if err := tx.QueryRowContext(ctx, `SELECT id, status FROM tasks WHERE public_id=?`, taskID).Scan(&taskPK, &status); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return model.PluginOutputReview{}, ErrNotFound
		}
		return model.PluginOutputReview{}, err
	}
	if status != model.TaskSucceeded && status != model.TaskFailed && status != model.TaskCancelled {
		return model.PluginOutputReview{}, fmt.Errorf("%w: task output is not terminal", ErrConflict)
	}

	currentRank := model.PluginOutputRankUnranked
	currentNotes := ""
	err = tx.QueryRowContext(ctx, `SELECT rank, notes FROM plugin_output_reviews WHERE task_id=?`, taskPK).
		Scan(&currentRank, &currentNotes)
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		return model.PluginOutputReview{}, err
	}
	if rank != nil {
		currentRank = *rank
	}
	if notes != nil {
		currentNotes = *notes
	}
	now := time.Now().UTC()
	if _, err := tx.ExecContext(ctx, `
INSERT INTO plugin_output_reviews(task_id, rank, notes, updated_at) VALUES(?, ?, ?, ?)
ON CONFLICT(task_id) DO UPDATE SET rank=excluded.rank, notes=excluded.notes, updated_at=excluded.updated_at`,
		taskPK, currentRank, currentNotes, formatTime(now)); err != nil {
		return model.PluginOutputReview{}, err
	}
	if err := tx.Commit(); err != nil {
		return model.PluginOutputReview{}, err
	}
	return s.GetPluginOutputReview(ctx, taskID)
}

func validPluginOutputRank(rank string) bool {
	switch rank {
	case model.PluginOutputRankUnranked, model.PluginOutputRankPassing, model.PluginOutputRankInformational,
		model.PluginOutputRankLow, model.PluginOutputRankMedium, model.PluginOutputRankHigh, model.PluginOutputRankCritical:
		return true
	default:
		return false
	}
}

func scanPluginOutputReview(row rowScanner) (model.PluginOutputReview, error) {
	var review model.PluginOutputReview
	var updated sql.NullString
	if err := row.Scan(&review.TaskID, &review.Rank, &review.Notes, &updated); err != nil {
		return model.PluginOutputReview{}, err
	}
	review.UpdatedAt = parseNullTime(updated)
	return review, nil
}

func scanPluginOutputReviews(rows *sql.Rows) ([]model.PluginOutputReview, error) {
	reviews := make([]model.PluginOutputReview, 0)
	for rows.Next() {
		review, err := scanPluginOutputReview(rows)
		if err != nil {
			return nil, err
		}
		reviews = append(reviews, review)
	}
	return reviews, rows.Err()
}

// GetTargetReport assembles all retained task and evidence records for a target.
func (s *Store) GetTargetReport(ctx context.Context, targetID string) (model.TargetReport, error) {
	target, err := s.GetTarget(ctx, targetID)
	if err != nil {
		return model.TargetReport{}, err
	}
	report := model.TargetReport{
		Target:              target,
		Tasks:               []model.Task{},
		PluginOutputReviews: []model.PluginOutputReview{},
		Attempts:            []model.TaskAttempt{},
		Events:              []model.TaskEvent{},
		Artifacts:           []model.Artifact{},
		Transactions:        []model.Transaction{},
		Observations:        []model.Observation{},
		Findings:            []model.Finding{},
	}
	report.Tasks, err = s.listTargetTasks(ctx, targetID)
	if err != nil {
		return model.TargetReport{}, err
	}
	for _, task := range report.Tasks {
		attempts, attemptErr := s.ListTaskAttempts(ctx, task.ID)
		if attemptErr != nil {
			return model.TargetReport{}, attemptErr
		}
		report.Attempts = append(report.Attempts, attempts...)
		events, eventErr := s.ListTaskEvents(ctx, task.ID)
		if eventErr != nil {
			return model.TargetReport{}, eventErr
		}
		report.Events = append(report.Events, events...)
	}
	if report.Artifacts, err = s.listArtifacts(ctx, targetID); err != nil {
		return model.TargetReport{}, err
	}
	if report.Transactions, err = s.listTransactions(ctx, targetID, 0); err != nil {
		return model.TargetReport{}, err
	}
	if report.Observations, err = s.listObservations(ctx, targetID); err != nil {
		return model.TargetReport{}, err
	}
	if report.Findings, err = s.listFindings(ctx, targetID); err != nil {
		return model.TargetReport{}, err
	}
	if report.PluginOutputReviews, err = s.listTargetPluginOutputReviews(ctx, targetID); err != nil {
		return model.TargetReport{}, err
	}
	return report, nil
}

// GetSessionReport assembles all retained execution and evidence records for a
// session using direct session-scoped queries.
func (s *Store) GetSessionReport(ctx context.Context, sessionID string) (model.SessionReport, error) {
	session, err := s.GetSession(ctx, sessionID)
	if err != nil {
		return model.SessionReport{}, err
	}
	report := model.SessionReport{
		Session:             session,
		Targets:             []model.Target{},
		Runs:                []model.Run{},
		Tasks:               []model.Task{},
		PluginOutputReviews: []model.PluginOutputReview{},
		Attempts:            []model.TaskAttempt{},
		Events:              []model.TaskEvent{},
		Artifacts:           []model.Artifact{},
		Transactions:        []model.Transaction{},
		Observations:        []model.Observation{},
		Findings:            []model.Finding{},
	}
	if report.Targets, err = s.ListTargets(ctx, sessionID); err != nil {
		return model.SessionReport{}, err
	}
	if report.Runs, err = s.ListRuns(ctx, sessionID); err != nil {
		return model.SessionReport{}, err
	}
	if report.Tasks, err = s.ListTasks(ctx, sessionID, ""); err != nil {
		return model.SessionReport{}, err
	}
	if report.Attempts, err = s.listSessionAttempts(ctx, sessionID); err != nil {
		return model.SessionReport{}, err
	}
	if report.Events, err = s.listSessionEvents(ctx, sessionID); err != nil {
		return model.SessionReport{}, err
	}
	if report.Artifacts, err = s.listSessionArtifacts(ctx, sessionID); err != nil {
		return model.SessionReport{}, err
	}
	if report.Transactions, err = s.ListTransactions(ctx, sessionID, ""); err != nil {
		return model.SessionReport{}, err
	}
	if report.Observations, err = s.listSessionObservations(ctx, sessionID); err != nil {
		return model.SessionReport{}, err
	}
	if report.Findings, err = s.listSessionFindings(ctx, sessionID); err != nil {
		return model.SessionReport{}, err
	}
	if report.PluginOutputReviews, err = s.listSessionPluginOutputReviews(ctx, sessionID); err != nil {
		return model.SessionReport{}, err
	}
	report.Summary = summarizeReport(report)
	return report, nil
}

func summarizeReport(report model.SessionReport) model.ReportSummary {
	summary := model.ReportSummary{
		Targets: len(report.Targets), Runs: len(report.Runs), Tasks: len(report.Tasks),
		Attempts:     len(report.Attempts),
		Transactions: len(report.Transactions), Artifacts: len(report.Artifacts),
		Observations: len(report.Observations), Findings: len(report.Findings),
	}
	for _, task := range report.Tasks {
		switch task.Status {
		case model.TaskQueued:
			summary.Queued++
		case model.TaskBlocked:
			summary.Blocked++
		case model.TaskRunning:
			summary.Running++
		case model.TaskSucceeded:
			summary.Succeeded++
		case model.TaskFailed:
			summary.Failed++
		case model.TaskCancelled:
			summary.Cancelled++
		}
	}
	return summary
}

func (s *Store) listSessionAttempts(ctx context.Context, sessionID string) ([]model.TaskAttempt, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT a.public_id, t.public_id, a.attempt_number, a.status, a.started_at, a.ended_at, a.error
FROM attempts a JOIN tasks t ON t.id=a.task_id JOIN runs r ON r.id=t.run_id
JOIN sessions s ON s.id=r.session_id WHERE s.public_id=? ORDER BY a.id`, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanTaskAttempts(rows)
}

func (s *Store) listSessionEvents(ctx context.Context, sessionID string) ([]model.TaskEvent, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT e.id, t.public_id, COALESCE(a.public_id,''), e.stream, e.message, e.created_at
FROM task_events e
JOIN tasks t ON t.id=e.task_id
JOIN runs r ON r.id=t.run_id
JOIN sessions s ON s.id=r.session_id
LEFT JOIN attempts a ON a.id=e.attempt_id
WHERE s.public_id=? ORDER BY e.id`, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	events := make([]model.TaskEvent, 0)
	for rows.Next() {
		var item model.TaskEvent
		var created string
		if err := rows.Scan(&item.ID, &item.TaskID, &item.AttemptID, &item.Stream, &item.Message, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		events = append(events, item)
	}
	return events, rows.Err()
}

func (s *Store) listSessionArtifacts(ctx context.Context, sessionID string) ([]model.Artifact, error) {
	rows, err := s.db.QueryContext(ctx, `
	SELECT a.public_id, COALESCE(t.public_id,''), tg.public_id, a.name, a.media_type, a.size, a.sha256, a.path, a.created_at
	FROM artifacts a
	LEFT JOIN tasks t ON t.id=a.task_id
	JOIN targets tg ON tg.id=a.target_id
	JOIN sessions s ON s.id=tg.session_id
	WHERE s.public_id=? ORDER BY a.id DESC`, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]model.Artifact, 0)
	for rows.Next() {
		var item model.Artifact
		var created string
		if err := rows.Scan(&item.ID, &item.TaskID, &item.TargetID, &item.Name, &item.MediaType, &item.Size, &item.SHA256, &item.Path, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		items = append(items, item)
	}
	return items, rows.Err()
}

func (s *Store) listSessionObservations(ctx context.Context, sessionID string) ([]model.Observation, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT o.public_id, t.public_id, tg.public_id, o.technique_code, o.kind, o.data, o.created_at
FROM observations o
JOIN tasks t ON t.id=o.task_id
JOIN targets tg ON tg.id=o.target_id
JOIN sessions s ON s.id=tg.session_id
WHERE s.public_id=? ORDER BY o.id DESC`, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]model.Observation, 0)
	for rows.Next() {
		var item model.Observation
		var created string
		if err := rows.Scan(&item.ID, &item.TaskID, &item.TargetID, &item.TechniqueCode, &item.Kind, &item.Data, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		items = append(items, item)
	}
	return items, rows.Err()
}

func (s *Store) listSessionFindings(ctx context.Context, sessionID string) ([]model.Finding, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT f.public_id, t.public_id, tg.public_id, f.technique_code, f.title, f.severity, f.description, f.created_at
FROM findings f
JOIN tasks t ON t.id=f.task_id
JOIN targets tg ON tg.id=f.target_id
JOIN sessions s ON s.id=tg.session_id
WHERE s.public_id=? ORDER BY f.id DESC`, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]model.Finding, 0)
	for rows.Next() {
		var item model.Finding
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

func (s *Store) listSessionPluginOutputReviews(ctx context.Context, sessionID string) ([]model.PluginOutputReview, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT t.public_id, COALESCE(v.rank, ?), COALESCE(v.notes, ''), v.updated_at
FROM tasks t JOIN runs r ON r.id=t.run_id JOIN sessions s ON s.id=r.session_id
LEFT JOIN plugin_output_reviews v ON v.task_id=t.id
WHERE s.public_id=? ORDER BY t.id DESC`, model.PluginOutputRankUnranked, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanPluginOutputReviews(rows)
}

func (s *Store) listTargetTasks(ctx context.Context, targetID string) ([]model.Task, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT t.public_id, r.public_id, tg.public_id, t.plugin_id, t.status, t.error,
       t.plugin_snapshot, t.created_at, t.started_at, t.ended_at
FROM tasks t JOIN runs r ON r.id=t.run_id JOIN targets tg ON tg.id=t.target_id
WHERE tg.public_id=? ORDER BY t.id DESC`, targetID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]model.Task, 0)
	for rows.Next() {
		item, err := scanTask(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

func (s *Store) listArtifacts(ctx context.Context, targetID string) ([]model.Artifact, error) {
	rows, err := s.db.QueryContext(ctx, `
	SELECT a.public_id, COALESCE(t.public_id,''), tg.public_id, a.name, a.media_type, a.size, a.sha256, a.path, a.created_at
	FROM artifacts a LEFT JOIN tasks t ON t.id=a.task_id JOIN targets tg ON tg.id=a.target_id
	WHERE tg.public_id=? ORDER BY a.id DESC`, targetID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]model.Artifact, 0)
	for rows.Next() {
		var item model.Artifact
		var created string
		if err := rows.Scan(&item.ID, &item.TaskID, &item.TargetID, &item.Name, &item.MediaType, &item.Size, &item.SHA256, &item.Path, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		items = append(items, item)
	}
	return items, rows.Err()
}

// GetArtifact returns artifact metadata by public ID.
func (s *Store) GetArtifact(ctx context.Context, artifactID string) (model.Artifact, error) {
	var item model.Artifact
	var created string
	err := s.db.QueryRowContext(ctx, `
	SELECT a.public_id, COALESCE(t.public_id,''), tg.public_id, a.name, a.media_type, a.size, a.sha256, a.path, a.created_at
	FROM artifacts a LEFT JOIN tasks t ON t.id=a.task_id JOIN targets tg ON tg.id=a.target_id
	WHERE a.public_id=?`, artifactID).
		Scan(&item.ID, &item.TaskID, &item.TargetID, &item.Name, &item.MediaType, &item.Size, &item.SHA256, &item.Path, &created)
	if errors.Is(err, sql.ErrNoRows) {
		return model.Artifact{}, ErrNotFound
	}
	if err != nil {
		return model.Artifact{}, err
	}
	item.CreatedAt = parseTime(created)
	return item, nil
}

func (s *Store) listTransactions(ctx context.Context, targetID string, limit int) ([]model.Transaction, error) {
	query := `
		SELECT tr.public_id, COALESCE(t.public_id,''), tg.public_id, tr.method, tr.url, tr.request_headers, tr.status_code,
		       tr.response_headers, COALESCE(source.public_id,''), COALESCE(request_body.public_id,''),
		       COALESCE(response_body.public_id,''), tr.duration_ms, tr.created_at
		FROM transactions tr LEFT JOIN tasks t ON t.id=tr.task_id JOIN targets tg ON tg.id=tr.target_id
		LEFT JOIN artifacts source ON source.id=tr.source_artifact_id
		LEFT JOIN artifacts request_body ON request_body.id=tr.request_body_artifact_id
		LEFT JOIN artifacts response_body ON response_body.id=tr.response_body_artifact_id
	WHERE tg.public_id=? ORDER BY tr.id DESC`
	args := []any{targetID}
	if limit > 0 {
		query += ` LIMIT ?`
		args = append(args, limit)
	}
	rows, err := s.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanTransactions(rows)
}

// ListTargetTransactions returns all transactions for one target, newest first.
func (s *Store) ListTargetTransactions(ctx context.Context, targetID string) ([]model.Transaction, error) {
	if _, err := s.GetTarget(ctx, targetID); err != nil {
		return nil, err
	}
	return s.listTransactions(ctx, targetID, 0)
}

// ListTargetTransactionsBounded returns at most limit transactions for an
// internal consumer that must place a hard bound on retained evidence.
func (s *Store) ListTargetTransactionsBounded(ctx context.Context, targetID string, limit int) ([]model.Transaction, error) {
	if limit < 1 {
		return nil, errors.New("transaction limit must be positive")
	}
	if _, err := s.GetTarget(ctx, targetID); err != nil {
		return nil, err
	}
	return s.listTransactions(ctx, targetID, limit)
}

// ListTransactions returns captured transactions for a session and optional
// target, newest first.
func (s *Store) ListTransactions(ctx context.Context, sessionID, targetID string) ([]model.Transaction, error) {
	query := `
		SELECT tr.public_id, COALESCE(t.public_id,''), tg.public_id, tr.method, tr.url, tr.request_headers, tr.status_code,
		       tr.response_headers, COALESCE(source.public_id,''), COALESCE(request_body.public_id,''),
		       COALESCE(response_body.public_id,''), tr.duration_ms, tr.created_at
		FROM transactions tr LEFT JOIN tasks t ON t.id=tr.task_id JOIN targets tg ON tg.id=tr.target_id
		JOIN sessions s ON s.id=tg.session_id
		LEFT JOIN artifacts source ON source.id=tr.source_artifact_id
		LEFT JOIN artifacts request_body ON request_body.id=tr.request_body_artifact_id
		LEFT JOIN artifacts response_body ON response_body.id=tr.response_body_artifact_id
	WHERE s.public_id=?`
	args := []any{sessionID}
	if targetID != "" {
		query += ` AND tg.public_id=?`
		args = append(args, targetID)
	}
	query += ` ORDER BY tr.id DESC`
	rows, err := s.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanTransactions(rows)
}

// TransactionFilter is a bounded search over persisted HTTP transactions.
type TransactionFilter struct {
	Search     string
	Method     string
	StatusCode *int
	Limit      int
	Offset     int
}

// SearchTransactions returns a deterministic page scoped by session, target,
// or both. Captured request and response bodies remain in the artifact store
// and are not loaded for list searches.
func (s *Store) SearchTransactions(ctx context.Context, sessionID, targetID string, filter TransactionFilter) (model.TransactionSearchResult, error) {
	if sessionID == "" && targetID == "" {
		return model.TransactionSearchResult{}, errors.New("transaction search requires a session or target")
	}
	if filter.Limit < 1 || filter.Limit > 1000 || filter.Offset < 0 {
		return model.TransactionSearchResult{}, errors.New("invalid transaction search bounds")
	}
	if sessionID != "" {
		if _, err := s.GetSession(ctx, sessionID); err != nil {
			return model.TransactionSearchResult{}, err
		}
	}
	if targetID != "" {
		target, err := s.GetTarget(ctx, targetID)
		if err != nil {
			return model.TransactionSearchResult{}, err
		}
		if sessionID != "" && target.SessionID != sessionID {
			return model.TransactionSearchResult{}, ErrNotFound
		}
	}

	where := make([]string, 0, 7)
	args := make([]any, 0, 12)
	if sessionID != "" {
		where = append(where, "s.public_id=?")
		args = append(args, sessionID)
	}
	if targetID != "" {
		where = append(where, "tg.public_id=?")
		args = append(args, targetID)
	}
	basePredicate := strings.Join(where, " AND ")
	result := model.TransactionSearchResult{Data: []model.Transaction{}}
	if err := s.db.QueryRowContext(ctx, `
SELECT COUNT(*) FROM transactions tr JOIN targets tg ON tg.id=tr.target_id
JOIN sessions s ON s.id=tg.session_id WHERE `+basePredicate, args...).Scan(&result.RecordsTotal); err != nil {
		return model.TransactionSearchResult{}, err
	}
	if filter.Search != "" {
		where = append(where, `(instr(lower(tr.url), lower(?)) > 0 OR instr(lower(tr.method), lower(?)) > 0
OR instr(lower(tr.request_headers), lower(?)) > 0 OR instr(lower(tr.response_headers), lower(?)) > 0)`)
		args = append(args, filter.Search, filter.Search, filter.Search, filter.Search)
	}
	if filter.Method != "" {
		where = append(where, "tr.method=?")
		args = append(args, filter.Method)
	}
	if filter.StatusCode != nil {
		where = append(where, "tr.status_code=?")
		args = append(args, *filter.StatusCode)
	}
	predicate := strings.Join(where, " AND ")
	if err := s.db.QueryRowContext(ctx, `
SELECT COUNT(*) FROM transactions tr JOIN targets tg ON tg.id=tr.target_id
JOIN sessions s ON s.id=tg.session_id WHERE `+predicate, args...).Scan(&result.RecordsFiltered); err != nil {
		return model.TransactionSearchResult{}, err
	}
	queryArgs := append(append([]any(nil), args...), filter.Limit, filter.Offset)
	rows, err := s.db.QueryContext(ctx, `
SELECT tr.public_id, COALESCE(t.public_id,''), tg.public_id, tr.method, tr.url, tr.request_headers, tr.status_code,
       tr.response_headers, COALESCE(source.public_id,''), COALESCE(request_body.public_id,''),
       COALESCE(response_body.public_id,''), tr.duration_ms, tr.created_at
FROM transactions tr LEFT JOIN tasks t ON t.id=tr.task_id JOIN targets tg ON tg.id=tr.target_id
JOIN sessions s ON s.id=tg.session_id
LEFT JOIN artifacts source ON source.id=tr.source_artifact_id
LEFT JOIN artifacts request_body ON request_body.id=tr.request_body_artifact_id
LEFT JOIN artifacts response_body ON response_body.id=tr.response_body_artifact_id
WHERE `+predicate+` ORDER BY tr.id DESC LIMIT ? OFFSET ?`, queryArgs...)
	if err != nil {
		return model.TransactionSearchResult{}, err
	}
	defer rows.Close()
	result.Data, err = scanTransactions(rows)
	if err != nil {
		return model.TransactionSearchResult{}, err
	}
	return result, nil
}

// GetTransaction returns one transaction owned by a target.
func (s *Store) GetTransaction(ctx context.Context, targetID, transactionID string) (model.Transaction, error) {
	row := s.db.QueryRowContext(ctx, `
SELECT tr.public_id, COALESCE(t.public_id,''), tg.public_id, tr.method, tr.url, tr.request_headers, tr.status_code,
       tr.response_headers, COALESCE(source.public_id,''), COALESCE(request_body.public_id,''),
       COALESCE(response_body.public_id,''), tr.duration_ms, tr.created_at
FROM transactions tr LEFT JOIN tasks t ON t.id=tr.task_id JOIN targets tg ON tg.id=tr.target_id
LEFT JOIN artifacts source ON source.id=tr.source_artifact_id
LEFT JOIN artifacts request_body ON request_body.id=tr.request_body_artifact_id
LEFT JOIN artifacts response_body ON response_body.id=tr.response_body_artifact_id
WHERE tg.public_id=? AND tr.public_id=?`, targetID, transactionID)
	item, err := scanTransaction(row)
	if errors.Is(err, sql.ErrNoRows) {
		return model.Transaction{}, ErrNotFound
	}
	return item, err
}

// DeleteTransaction removes one transaction and unreferenced files imported
// with it. Content-addressed bytes are retained for safe deduplication.
func (s *Store) DeleteTransaction(ctx context.Context, targetID, transactionID string) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	result, err := tx.ExecContext(ctx, `
DELETE FROM transactions
WHERE public_id=? AND target_id=(SELECT id FROM targets WHERE public_id=?)`, transactionID, targetID)
	if err != nil {
		return err
	}
	if count, _ := result.RowsAffected(); count == 0 {
		return ErrNotFound
	}
	if _, err := tx.ExecContext(ctx, `
DELETE FROM artifacts
WHERE task_id IS NULL AND target_id=(SELECT id FROM targets WHERE public_id=?)
  AND NOT EXISTS (SELECT 1 FROM transactions WHERE source_artifact_id=artifacts.id
                  OR request_body_artifact_id=artifacts.id OR response_body_artifact_id=artifacts.id)`, targetID); err != nil {
		return err
	}
	return tx.Commit()
}

func scanTransactions(rows *sql.Rows) ([]model.Transaction, error) {
	items := make([]model.Transaction, 0)
	for rows.Next() {
		item, err := scanTransaction(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

func scanTransaction(row rowScanner) (model.Transaction, error) {
	var item model.Transaction
	var created string
	err := row.Scan(&item.ID, &item.TaskID, &item.TargetID, &item.Method, &item.URL,
		&item.RequestHeaders, &item.StatusCode, &item.ResponseHeaders, &item.SourceArtifactID,
		&item.RequestBodyArtifactID, &item.ResponseBodyArtifactID, &item.DurationMS, &created)
	item.CreatedAt = parseTime(created)
	return item, err
}

func (s *Store) listObservations(ctx context.Context, targetID string) ([]model.Observation, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT o.public_id, t.public_id, tg.public_id, o.technique_code, o.kind, o.data, o.created_at
FROM observations o JOIN tasks t ON t.id=o.task_id JOIN targets tg ON tg.id=o.target_id
WHERE tg.public_id=? ORDER BY o.id DESC`, targetID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]model.Observation, 0)
	for rows.Next() {
		var item model.Observation
		var created string
		if err := rows.Scan(&item.ID, &item.TaskID, &item.TargetID, &item.TechniqueCode, &item.Kind, &item.Data, &created); err != nil {
			return nil, err
		}
		item.CreatedAt = parseTime(created)
		items = append(items, item)
	}
	return items, rows.Err()
}

func (s *Store) listFindings(ctx context.Context, targetID string) ([]model.Finding, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT f.public_id, t.public_id, tg.public_id, f.technique_code, f.title, f.severity, f.description, f.created_at
FROM findings f JOIN tasks t ON t.id=f.task_id JOIN targets tg ON tg.id=f.target_id
WHERE tg.public_id=? ORDER BY f.id DESC`, targetID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]model.Finding, 0)
	for rows.Next() {
		var item model.Finding
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

func (s *Store) listTargetPluginOutputReviews(ctx context.Context, targetID string) ([]model.PluginOutputReview, error) {
	rows, err := s.db.QueryContext(ctx, `
SELECT t.public_id, COALESCE(v.rank, ?), COALESCE(v.notes, ''), v.updated_at
FROM tasks t JOIN targets tg ON tg.id=t.target_id
LEFT JOIN plugin_output_reviews v ON v.task_id=t.id
WHERE tg.public_id=? ORDER BY t.id DESC`, model.PluginOutputRankUnranked, targetID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanPluginOutputReviews(rows)
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

func nullableTime(value *time.Time) any {
	if value == nil {
		return nil
	}
	return formatTime(*value)
}
