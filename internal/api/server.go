package api

import (
	"embed"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"log/slog"
	"mime"
	"net/http"
	"path/filepath"
	"strings"

	"github.com/owtf/owtf/internal/artifact"
	"github.com/owtf/owtf/internal/plugin"
	reportoutput "github.com/owtf/owtf/internal/report"
	"github.com/owtf/owtf/internal/runner"
	"github.com/owtf/owtf/internal/store"
	targetvalue "github.com/owtf/owtf/internal/target"
)

//go:embed ui/*
var uiFiles embed.FS

// Server owns the OWTF HTTP handlers and application services.
type Server struct {
	store     *store.Store
	artifacts *artifact.Store
	catalog   *plugin.Catalog
	runner    *runner.Runner
}

// New returns the complete OWTF HTTP handler. Authentication is intentionally
// outside this boundary and may be supplied by a reverse proxy.
func New(database *store.Store, artifacts *artifact.Store, catalog *plugin.Catalog, taskRunner *runner.Runner) http.Handler {
	server := &Server{store: database, artifacts: artifacts, catalog: catalog, runner: taskRunner}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /debug/health", server.health)
	mux.HandleFunc("GET /api/v2/health", server.health)
	mux.HandleFunc("GET /api/v2/sessions", server.listSessions)
	mux.HandleFunc("POST /api/v2/sessions", server.createSession)
	mux.HandleFunc("GET /api/v2/sessions/{sessionID}", server.getSession)
	mux.HandleFunc("GET /api/v2/sessions/{sessionID}/report", server.sessionReport)
	mux.HandleFunc("GET /api/v2/sessions/{sessionID}/export", server.sessionExport)
	mux.HandleFunc("GET /api/v2/sessions/{sessionID}/targets", server.listTargets)
	mux.HandleFunc("POST /api/v2/sessions/{sessionID}/targets", server.addTargets)
	mux.HandleFunc("GET /api/v2/targets/{targetID}", server.getTarget)
	mux.HandleFunc("DELETE /api/v2/targets/{targetID}", server.deleteTarget)
	mux.HandleFunc("GET /api/v2/targets/{targetID}/report", server.targetReport)
	mux.HandleFunc("GET /api/v2/plugins", server.listPlugins)
	mux.HandleFunc("POST /api/v2/runs", server.createRun)
	mux.HandleFunc("GET /api/v2/runs", server.listRuns)
	mux.HandleFunc("GET /api/v2/runs/{runID}", server.getRun)
	mux.HandleFunc("GET /api/v2/workers", server.listWorkers)
	mux.HandleFunc("GET /api/v2/tasks", server.listTasks)
	mux.HandleFunc("GET /api/v2/tasks/{taskID}", server.getTask)
	mux.HandleFunc("GET /api/v2/tasks/{taskID}/events", server.taskEvents)
	mux.HandleFunc("POST /api/v2/tasks/{taskID}/cancel", server.cancelTask)
	mux.HandleFunc("GET /api/v2/transactions", server.listTransactions)
	mux.HandleFunc("GET /api/v2/artifacts/{artifactID}", server.getArtifact)
	staticFS, err := fs.Sub(uiFiles, "ui")
	if err != nil {
		panic(err)
	}
	mux.Handle("GET /assets/", http.StripPrefix("/assets/", http.FileServerFS(staticFS)))
	mux.HandleFunc("GET /", server.app)
	return server.middleware(mux)
}

func (s *Server) middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Security-Policy", "default-src 'self'; connect-src 'self'; img-src 'self'; script-src 'self'; style-src 'self'")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Referrer-Policy", "no-referrer")
		next.ServeHTTP(w, r)
	})
}

func (s *Server) app(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" && r.URL.Path != "/work" && r.URL.Path != "/workers" && r.URL.Path != "/transactions" && !strings.HasPrefix(r.URL.Path, "/targets/") {
		http.NotFound(w, r)
		return
	}
	data, err := uiFiles.ReadFile("ui/index.html")
	if err != nil {
		s.internalError(w, err)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	_, _ = w.Write(data)
}

func (s *Server) health(w http.ResponseWriter, r *http.Request) {
	if _, err := s.store.ListSessions(r.Context()); err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) createSession(w http.ResponseWriter, r *http.Request) {
	var input struct {
		Name string `json:"name"`
	}
	if err := decodeJSON(w, r, &input); err != nil {
		return
	}
	item, err := s.store.CreateSession(r.Context(), input.Name)
	if err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, item)
}

func (s *Server) listSessions(w http.ResponseWriter, r *http.Request) {
	items, err := s.store.ListSessions(r.Context())
	if err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, items)
}

func (s *Server) getSession(w http.ResponseWriter, r *http.Request) {
	item, err := s.store.GetSession(r.Context(), r.PathValue("sessionID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, item)
}

func (s *Server) sessionReport(w http.ResponseWriter, r *http.Request) {
	report, err := s.store.GetSessionReport(r.Context(), r.PathValue("sessionID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, report)
}

func (s *Server) sessionExport(w http.ResponseWriter, r *http.Request) {
	session, err := s.store.GetSessionReport(r.Context(), r.PathValue("sessionID"))
	if s.handleStoreError(w, err) {
		return
	}
	w.Header().Set("Content-Type", "application/zip")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="owtf-%s.zip"`, session.Session.ID))
	w.Header().Set("Cache-Control", "no-store")
	if err := reportoutput.WriteSessionArchive(w, session, s.artifacts); err != nil {
		slog.Error("write session export", "session_id", session.Session.ID, "error", err)
	}
}

func (s *Server) listTargets(w http.ResponseWriter, r *http.Request) {
	items, err := s.store.ListTargets(r.Context(), r.PathValue("sessionID"))
	if err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, items)
}

type invalidTarget struct {
	Input string `json:"input"`
	Error string `json:"error"`
}

func (s *Server) addTargets(w http.ResponseWriter, r *http.Request) {
	var input struct {
		Targets []string `json:"targets"`
	}
	if err := decodeJSON(w, r, &input); err != nil {
		return
	}
	if len(input.Targets) == 0 {
		writeError(w, http.StatusBadRequest, "at least one target is required")
		return
	}
	normalized := make([]targetvalue.Normalized, 0, len(input.Targets))
	invalid := make([]invalidTarget, 0)
	for _, raw := range input.Targets {
		item, err := targetvalue.Normalize(raw)
		if err != nil {
			invalid = append(invalid, invalidTarget{Input: raw, Error: err.Error()})
			continue
		}
		normalized = append(normalized, item)
	}
	result, err := s.store.AddTargets(r.Context(), r.PathValue("sessionID"), normalized)
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"created": result.Created, "duplicates": result.Duplicates, "invalid": invalid,
	})
}

func (s *Server) getTarget(w http.ResponseWriter, r *http.Request) {
	item, err := s.store.GetTarget(r.Context(), r.PathValue("targetID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, item)
}

func (s *Server) deleteTarget(w http.ResponseWriter, r *http.Request) {
	err := s.store.DeleteTarget(r.Context(), r.PathValue("targetID"))
	if s.handleStoreError(w, err) {
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) targetReport(w http.ResponseWriter, r *http.Request) {
	report, err := s.store.GetTargetReport(r.Context(), r.PathValue("targetID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, report)
}

func (s *Server) listPlugins(w http.ResponseWriter, r *http.Request) {
	items, err := s.store.ListPlugins(r.Context())
	if err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, items)
}

func (s *Server) createRun(w http.ResponseWriter, r *http.Request) {
	var input struct {
		SessionID string   `json:"session_id"`
		TargetIDs []string `json:"target_ids"`
		PluginIDs []string `json:"plugin_ids"`
	}
	if err := decodeJSON(w, r, &input); err != nil {
		return
	}
	if input.SessionID == "" || len(input.TargetIDs) == 0 || len(input.PluginIDs) == 0 {
		writeError(w, http.StatusBadRequest, "session_id, target_ids, and plugin_ids are required")
		return
	}
	targetKinds := make(map[string]string, len(input.TargetIDs))
	for _, targetID := range input.TargetIDs {
		target, err := s.store.GetTarget(r.Context(), targetID)
		if s.handleStoreError(w, err) {
			return
		}
		if target.SessionID != input.SessionID {
			writeError(w, http.StatusBadRequest, fmt.Sprintf("target %s does not belong to the session", targetID))
			return
		}
		targetKinds[targetID] = target.Kind
	}
	specs := make([]store.TaskSpec, 0, len(input.TargetIDs)*len(input.PluginIDs))
	for _, pluginID := range input.PluginIDs {
		entry, ok := s.catalog.Get(pluginID)
		if !ok {
			writeError(w, http.StatusBadRequest, fmt.Sprintf("plugin %s does not exist", pluginID))
			return
		}
		if entry.Availability != "ready" {
			writeError(w, http.StatusConflict, fmt.Sprintf("plugin %s is unavailable: %s", pluginID, entry.Reason))
			return
		}
		for _, targetID := range input.TargetIDs {
			if !entry.SupportsTarget(targetKinds[targetID]) {
				writeError(w, http.StatusBadRequest, fmt.Sprintf("plugin %s does not support %s targets", pluginID, targetKinds[targetID]))
				return
			}
		}
		snapshot, err := entry.Snapshot()
		if err != nil {
			s.internalError(w, err)
			return
		}
		for _, targetID := range input.TargetIDs {
			specs = append(specs, store.TaskSpec{
				TargetID: targetID, PluginID: pluginID, PluginVersion: entry.Manifest.Metadata.Version,
				PluginSnapshot: snapshot,
			})
		}
	}
	run, tasks, err := s.store.CreateRun(r.Context(), input.SessionID, specs)
	if s.handleStoreError(w, err) {
		return
	}
	ids := make([]string, 0, len(tasks))
	for _, task := range tasks {
		ids = append(ids, task.ID)
	}
	if err := s.runner.Submit(r.Context(), ids); err != nil {
		s.internalError(w, fmt.Errorf("queue tasks: %w", err))
		return
	}
	writeJSON(w, http.StatusAccepted, map[string]any{"run": run, "tasks": tasks})
}

func (s *Server) listRuns(w http.ResponseWriter, r *http.Request) {
	sessionID := r.URL.Query().Get("session_id")
	if sessionID == "" {
		writeError(w, http.StatusBadRequest, "session_id is required")
		return
	}
	if _, err := s.store.GetSession(r.Context(), sessionID); s.handleStoreError(w, err) {
		return
	}
	items, err := s.store.ListRuns(r.Context(), sessionID)
	if err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, items)
}

func (s *Server) getRun(w http.ResponseWriter, r *http.Request) {
	item, err := s.store.GetRun(r.Context(), r.PathValue("runID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, item)
}

func (s *Server) listTasks(w http.ResponseWriter, r *http.Request) {
	items, err := s.store.ListTasks(r.Context(), r.URL.Query().Get("session_id"), r.URL.Query().Get("status"))
	if err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, items)
}

func (s *Server) listWorkers(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, s.runner.Workers())
}

func (s *Server) getTask(w http.ResponseWriter, r *http.Request) {
	item, err := s.store.GetTask(r.Context(), r.PathValue("taskID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, item)
}

func (s *Server) cancelTask(w http.ResponseWriter, r *http.Request) {
	item, err := s.runner.Cancel(r.Context(), r.PathValue("taskID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, item)
}

func (s *Server) taskEvents(w http.ResponseWriter, r *http.Request) {
	if _, err := s.store.GetTask(r.Context(), r.PathValue("taskID")); s.handleStoreError(w, err) {
		return
	}
	items, err := s.store.ListTaskEvents(r.Context(), r.PathValue("taskID"))
	if err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, items)
}

func (s *Server) listTransactions(w http.ResponseWriter, r *http.Request) {
	sessionID := r.URL.Query().Get("session_id")
	if sessionID == "" {
		writeError(w, http.StatusBadRequest, "session_id is required")
		return
	}
	if _, err := s.store.GetSession(r.Context(), sessionID); s.handleStoreError(w, err) {
		return
	}
	items, err := s.store.ListHTTPExchanges(r.Context(), sessionID, r.URL.Query().Get("target_id"))
	if err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, items)
}

func (s *Server) getArtifact(w http.ResponseWriter, r *http.Request) {
	item, err := s.store.GetArtifact(r.Context(), r.PathValue("artifactID"))
	if s.handleStoreError(w, err) {
		return
	}
	file, err := s.artifacts.Open(item.Path)
	if err != nil {
		s.internalError(w, err)
		return
	}
	defer file.Close()
	mediaType := item.MediaType
	if mediaType == "" {
		mediaType = mime.TypeByExtension(filepath.Ext(item.Name))
	}
	if mediaType == "" {
		mediaType = "application/octet-stream"
	}
	w.Header().Set("Content-Type", mediaType)
	w.Header().Set("Content-Disposition", fmt.Sprintf(`inline; filename=%q`, filepath.Base(item.Name)))
	http.ServeContent(w, r, item.Name, item.CreatedAt, file)
}

func (s *Server) handleStoreError(w http.ResponseWriter, err error) bool {
	if err == nil {
		return false
	}
	if errors.Is(err, store.ErrNotFound) {
		writeError(w, http.StatusNotFound, "not found")
		return true
	}
	s.internalError(w, err)
	return true
}

func (s *Server) internalError(w http.ResponseWriter, err error) {
	slog.Error("api request failed", "error", err)
	writeError(w, http.StatusInternalServerError, "internal server error")
}

func decodeJSON(w http.ResponseWriter, r *http.Request, destination any) error {
	decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(destination); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON: "+err.Error())
		return err
	}
	return nil
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(value); err != nil {
		slog.Error("write JSON response", "error", err)
	}
}

func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]string{"error": message})
}
