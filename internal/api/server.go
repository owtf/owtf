package api

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"mime"
	"net/http"
	"path"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/owtf/owtf/internal/artifact"
	owtfconfig "github.com/owtf/owtf/internal/config"
	"github.com/owtf/owtf/internal/har"
	helpinfo "github.com/owtf/owtf/internal/help"
	"github.com/owtf/owtf/internal/model"
	"github.com/owtf/owtf/internal/plugin"
	"github.com/owtf/owtf/internal/profile"
	reportoutput "github.com/owtf/owtf/internal/report"
	"github.com/owtf/owtf/internal/runner"
	"github.com/owtf/owtf/internal/store"
	targetvalue "github.com/owtf/owtf/internal/target"
)

// Server owns the OWTF HTTP handlers and application services.
type Server struct {
	store          *store.Store
	artifacts      *artifact.Store
	catalog        *plugin.Catalog
	profiles       *profile.Catalog
	help           *helpinfo.Catalog
	defaultProfile string
	runner         *runner.Runner
	runtimeConfig  *owtfconfig.Config
}

// Config supplies the services owned by one API server.
type Config struct {
	Store          *store.Store
	Artifacts      *artifact.Store
	Plugins        *plugin.Catalog
	Profiles       *profile.Catalog
	Help           *helpinfo.Catalog
	DefaultProfile string
	Runner         *runner.Runner
	// RuntimeConfig is the effective startup configuration, after overrides.
	RuntimeConfig *owtfconfig.Config
}

// New returns the complete OWTF HTTP handler. Authentication is intentionally
// outside this boundary and may be supplied by a reverse proxy.
func New(config Config) http.Handler {
	if config.Profiles == nil {
		config.Profiles = profile.Empty()
	}
	if config.Help == nil {
		config.Help = helpinfo.Default()
	}
	server := &Server{
		store: config.Store, artifacts: config.Artifacts, catalog: config.Plugins,
		profiles: config.Profiles, help: config.Help, defaultProfile: config.DefaultProfile, runner: config.Runner,
	}
	if config.RuntimeConfig != nil {
		redacted := config.RuntimeConfig.Redacted()
		server.runtimeConfig = &redacted
	}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /debug/health", server.health)
	mux.HandleFunc("GET /api/v2/health", server.health)
	mux.HandleFunc("GET /api/v2/config", server.getConfig)
	mux.HandleFunc("POST /api/v2/config/validate", server.validateConfig)
	proxyAddress := ""
	if config.RuntimeConfig != nil {
		proxyAddress = config.RuntimeConfig.Proxy.APIAddress
	}
	proxyHandler := proxyAPI(proxyAddress)
	for _, method := range []string{"GET", "POST", "PUT", "PATCH", "DELETE"} {
		mux.Handle(method+" /api/v2/proxy/", proxyHandler)
	}
	mux.HandleFunc("GET /api/v2/sessions", server.listSessions)
	mux.HandleFunc("POST /api/v2/sessions", server.createSession)
	mux.HandleFunc("GET /api/v2/sessions/{sessionID}", server.getSession)
	mux.HandleFunc("DELETE /api/v2/sessions/{sessionID}", server.deleteSession)
	mux.HandleFunc("GET /api/v2/sessions/{sessionID}/report", server.sessionReport)
	mux.HandleFunc("GET /api/v2/sessions/{sessionID}/export", server.sessionExport)
	mux.HandleFunc("GET /api/v2/sessions/{sessionID}/targets", server.listTargets)
	mux.HandleFunc("GET /api/v2/sessions/{sessionID}/targets/search", server.searchTargets)
	mux.HandleFunc("POST /api/v2/sessions/{sessionID}/targets", server.addTargets)
	mux.HandleFunc("GET /api/v2/targets/{targetID}", server.getTarget)
	mux.HandleFunc("PATCH /api/v2/targets/{targetID}", server.updateTarget)
	mux.HandleFunc("DELETE /api/v2/targets/{targetID}", server.deleteTarget)
	mux.HandleFunc("GET /api/v2/targets/{targetID}/report", server.targetReport)
	mux.HandleFunc("GET /api/v2/targets/{targetID}/urls", server.listURLs)
	mux.HandleFunc("GET /api/v2/targets/{targetID}/urls/search", server.searchURLs)
	mux.HandleFunc("GET /api/v2/plugins", server.listPlugins)
	mux.HandleFunc("GET /api/v2/profiles", server.listProfiles)
	mux.HandleFunc("GET /api/v2/profiles/{profileName}", server.getProfile)
	mux.HandleFunc("GET /api/v2/help", server.getHelp)
	mux.HandleFunc("POST /api/v2/runs", server.createRun)
	mux.HandleFunc("GET /api/v2/runs", server.listRuns)
	mux.HandleFunc("GET /api/v2/runs/{runID}", server.getRun)
	mux.HandleFunc("GET /api/v2/workers", server.listWorkers)
	mux.HandleFunc("GET /api/v2/metrics", server.metrics)
	mux.HandleFunc("GET /api/v2/tasks", server.listTasks)
	mux.HandleFunc("GET /api/v2/tasks/{taskID}", server.getTask)
	mux.HandleFunc("GET /api/v2/tasks/{taskID}/attempts", server.taskAttempts)
	mux.HandleFunc("GET /api/v2/tasks/{taskID}/events", server.taskEvents)
	mux.HandleFunc("GET /api/v2/tasks/{taskID}/review", server.pluginOutputReview)
	mux.HandleFunc("PATCH /api/v2/tasks/{taskID}/review", server.updatePluginOutputReview)
	mux.HandleFunc("GET /api/v2/tasks/{taskID}/review/history", server.pluginOutputReviewHistory)
	mux.HandleFunc("POST /api/v2/tasks/{taskID}/cancel", server.cancelTask)
	mux.HandleFunc("POST /api/v2/tasks/{taskID}/pause", server.pauseTask)
	mux.HandleFunc("POST /api/v2/tasks/{taskID}/resume", server.resumeTask)
	mux.HandleFunc("DELETE /api/v2/tasks/{taskID}", server.removeTask)
	mux.HandleFunc("PUT /api/v2/worklist/order", server.reorderWorklist)
	mux.HandleFunc("GET /api/v2/transactions", server.listTransactions)
	mux.HandleFunc("GET /api/v2/transactions/search", server.searchTransactions)
	mux.HandleFunc("GET /api/v2/targets/{targetID}/transactions", server.listTargetTransactions)
	mux.HandleFunc("GET /api/v2/targets/{targetID}/transactions/search", server.searchTargetTransactions)
	mux.HandleFunc("POST /api/v2/targets/{targetID}/transactions/import", server.importTransactions)
	mux.HandleFunc("GET /api/v2/targets/{targetID}/transactions/{transactionID}", server.getTransaction)
	mux.HandleFunc("DELETE /api/v2/targets/{targetID}/transactions/{transactionID}", server.deleteTransaction)
	mux.HandleFunc("GET /api/v2/artifacts/{artifactID}", server.getArtifact)
	return server.middleware(mux)
}

func (s *Server) listProfiles(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, s.profiles.List())
}

func (s *Server) getProfile(w http.ResponseWriter, r *http.Request) {
	item, ok := s.profiles.Get(r.PathValue("profileName"))
	if !ok {
		writeError(w, http.StatusNotFound, "profile not found")
		return
	}
	writeJSON(w, http.StatusOK, item)
}

func (s *Server) getHelp(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, s.help.Snapshot())
}

func (s *Server) middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Security-Policy", "default-src 'self'; connect-src 'self'; img-src 'self'; script-src 'self'; style-src 'self'")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Referrer-Policy", "no-referrer")
		next.ServeHTTP(w, r)
	})
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

func (s *Server) deleteSession(w http.ResponseWriter, r *http.Request) {
	if s.handleStoreError(w, s.store.DeleteSession(r.Context(), r.PathValue("sessionID"))) {
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) sessionReport(w http.ResponseWriter, r *http.Request) {
	report, err := s.store.GetSessionReport(r.Context(), r.PathValue("sessionID"), r.URL.Query()["disposition"]...)
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, report)
}

func (s *Server) sessionExport(w http.ResponseWriter, r *http.Request) {
	session, err := s.store.GetSessionReport(r.Context(), r.PathValue("sessionID"), r.URL.Query()["disposition"]...)
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
	if _, err := s.store.GetSession(r.Context(), r.PathValue("sessionID")); s.handleStoreError(w, err) {
		return
	}
	items, err := s.store.ListTargets(r.Context(), r.PathValue("sessionID"))
	if err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, items)
}

func (s *Server) searchTargets(w http.ResponseWriter, r *http.Request) {
	filter, err := targetFilter(r)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	result, err := s.store.SearchTargets(r.Context(), r.PathValue("sessionID"), filter)
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, result)
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

func (s *Server) updateTarget(w http.ResponseWriter, r *http.Request) {
	var input struct {
		Scope *bool `json:"scope"`
	}
	if err := decodeJSON(w, r, &input); err != nil {
		return
	}
	if input.Scope == nil {
		writeError(w, http.StatusBadRequest, "scope is required")
		return
	}
	item, err := s.store.UpdateTargetScope(r.Context(), r.PathValue("targetID"), *input.Scope)
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
	getReport := s.store.GetTargetReport
	if r.URL.Query().Get("group") == "host" {
		getReport = s.store.GetTargetGroupReport
	}
	report, err := getReport(r.Context(), r.PathValue("targetID"), r.URL.Query()["disposition"]...)
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
	group := r.URL.Query().Get("group")
	types := stringSet(r.URL.Query()["type"])
	filtered := items[:0]
	for _, item := range items {
		if group != "" && item.Group != group {
			continue
		}
		if len(types) != 0 && !types[item.Type] {
			continue
		}
		filtered = append(filtered, item)
	}
	writeJSON(w, http.StatusOK, filtered)
}

func (s *Server) createRun(w http.ResponseWriter, r *http.Request) {
	var input struct {
		SessionID    string                    `json:"session_id"`
		TargetIDs    []string                  `json:"target_ids"`
		PluginIDs    []string                  `json:"plugin_ids"`
		PluginGroup  string                    `json:"plugin_group"`
		PluginTypes  []string                  `json:"plugin_types"`
		Profile      string                    `json:"profile"`
		PluginInputs map[string]map[string]any `json:"plugin_inputs"`
	}
	if err := decodeJSON(w, r, &input); err != nil {
		return
	}
	input.SessionID = strings.TrimSpace(input.SessionID)
	input.TargetIDs = uniqueStrings(input.TargetIDs)
	input.PluginIDs = uniqueStrings(input.PluginIDs)
	input.PluginGroup = strings.TrimSpace(input.PluginGroup)
	input.PluginTypes = uniqueStrings(input.PluginTypes)
	input.Profile = strings.TrimSpace(input.Profile)
	groupLaunch := input.PluginGroup != ""
	if input.SessionID == "" || len(input.TargetIDs) == 0 {
		writeError(w, http.StatusBadRequest, "session_id and target_ids are required")
		return
	}
	if (len(input.PluginIDs) == 0 && !groupLaunch) || (len(input.PluginIDs) != 0 && groupLaunch) {
		writeError(w, http.StatusBadRequest, "provide either plugin_ids or plugin_group")
		return
	}
	if !groupLaunch && len(input.PluginTypes) != 0 {
		writeError(w, http.StatusBadRequest, "plugin_types requires plugin_group")
		return
	}
	if !groupLaunch && input.Profile != "" {
		writeError(w, http.StatusBadRequest, "profile requires plugin_group")
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
	entries := make([]plugin.Entry, 0, len(input.PluginIDs))
	if groupLaunch {
		pluginTypes, err := expandPluginTypes(input.PluginTypes)
		if err != nil {
			writeError(w, http.StatusBadRequest, err.Error())
			return
		}
		entries = s.catalog.EntriesByGroupType(input.PluginGroup, pluginTypes)
		if len(entries) == 0 {
			writeError(w, http.StatusBadRequest, "no plugins match the requested group and types")
			return
		}
		if input.Profile == "" {
			input.Profile = s.defaultProfile
		}
		if input.Profile != "" {
			entries, err = s.profiles.Order(input.Profile, entries)
			if err != nil {
				writeError(w, http.StatusBadRequest, err.Error())
				return
			}
		}
	} else {
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
			entries = append(entries, entry)
		}
	}

	selected := make(map[string]bool, len(entries))
	for _, entry := range entries {
		selected[entry.Manifest.Metadata.ID] = true
	}
	unselected := make([]string, 0)
	for pluginID := range input.PluginInputs {
		if !selected[pluginID] {
			unselected = append(unselected, pluginID)
		}
	}
	if len(unselected) != 0 {
		sort.Strings(unselected)
		writeError(w, http.StatusBadRequest, fmt.Sprintf("plugin inputs provided for unselected plugins: %s", strings.Join(unselected, ", ")))
		return
	}
	specs := make([]store.TaskSpec, 0, len(input.TargetIDs)*len(entries))
	for _, entry := range entries {
		snapshot, err := entry.Snapshot(input.PluginInputs[entry.Manifest.Metadata.ID])
		if err != nil {
			writeError(w, http.StatusBadRequest, fmt.Sprintf("plugin %s inputs: %v", entry.Manifest.Metadata.ID, err))
			return
		}
		for _, targetID := range input.TargetIDs {
			spec := store.TaskSpec{
				TargetID: targetID, PluginID: entry.Manifest.Metadata.ID, PluginVersion: entry.Manifest.Metadata.Version,
				PluginSnapshot: snapshot, Status: model.TaskQueued,
			}
			if groupLaunch && entry.Availability != "ready" {
				spec.Status = model.TaskBlocked
				spec.Error = entry.Reason
			} else if groupLaunch && !entry.SupportsTarget(targetKinds[targetID]) {
				spec.Status = model.TaskBlocked
				spec.Error = fmt.Sprintf("plugin does not support %s targets", targetKinds[targetID])
			}
			specs = append(specs, spec)
		}
	}
	run, tasks, err := s.store.CreateRun(r.Context(), input.SessionID, input.Profile, specs)
	if s.handleStoreError(w, err) {
		return
	}
	ids := make([]string, 0, len(tasks))
	for _, task := range tasks {
		if task.Status == model.TaskQueued {
			ids = append(ids, task.ID)
		}
	}
	if len(ids) != 0 {
		if err := s.runner.Submit(ids); err != nil {
			s.internalError(w, fmt.Errorf("queue tasks: %w", err))
			return
		}
	}
	writeJSON(w, http.StatusAccepted, map[string]any{"run": run, "tasks": tasks})
}

func expandPluginTypes(values []string) ([]string, error) {
	values = uniqueStrings(values)
	if len(values) == 0 || (len(values) == 1 && values[0] == "all") {
		return nil, nil
	}
	if len(values) == 1 && values[0] == "quiet" {
		return []string{"passive", "semi_passive"}, nil
	}
	for _, value := range values {
		if value == "all" || value == "quiet" {
			return nil, fmt.Errorf("plugin type %q cannot be combined with other types", value)
		}
	}
	return values, nil
}

func uniqueStrings(values []string) []string {
	seen := make(map[string]bool, len(values))
	result := make([]string, 0, len(values))
	for _, value := range values {
		value = strings.TrimSpace(value)
		if value != "" && !seen[value] {
			seen[value] = true
			result = append(result, value)
		}
	}
	return result
}

func stringSet(values []string) map[string]bool {
	result := make(map[string]bool, len(values))
	for _, value := range uniqueStrings(values) {
		result[value] = true
	}
	return result
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

func (s *Server) metrics(w http.ResponseWriter, r *http.Request) {
	metrics, err := s.store.ExecutionMetrics(r.Context())
	if err != nil {
		s.internalError(w, err)
		return
	}
	for _, worker := range s.runner.Workers() {
		metrics.Workers.Total++
		if worker.Status == "running" {
			metrics.Workers.Running++
		} else {
			metrics.Workers.Idle++
		}
		metrics.Workers.Completed += worker.Completed
		metrics.Workers.Failed += worker.Failed
		metrics.Workers.Cancelled += worker.Cancelled
	}
	writeJSON(w, http.StatusOK, metrics)
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

func (s *Server) pauseTask(w http.ResponseWriter, r *http.Request) {
	item, err := s.runner.Pause(r.Context(), r.PathValue("taskID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, item)
}

func (s *Server) resumeTask(w http.ResponseWriter, r *http.Request) {
	item, err := s.runner.Resume(r.Context(), r.PathValue("taskID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, item)
}

func (s *Server) removeTask(w http.ResponseWriter, r *http.Request) {
	if s.handleStoreError(w, s.runner.Remove(r.Context(), r.PathValue("taskID"))) {
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) reorderWorklist(w http.ResponseWriter, r *http.Request) {
	var input struct {
		SessionID string   `json:"session_id"`
		TaskIDs   []string `json:"task_ids"`
	}
	if err := decodeJSON(w, r, &input); err != nil {
		return
	}
	items, err := s.runner.Reorder(r.Context(), strings.TrimSpace(input.SessionID), input.TaskIDs)
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, items)
}

func (s *Server) taskAttempts(w http.ResponseWriter, r *http.Request) {
	if _, err := s.store.GetTask(r.Context(), r.PathValue("taskID")); s.handleStoreError(w, err) {
		return
	}
	items, err := s.store.ListTaskAttempts(r.Context(), r.PathValue("taskID"))
	if err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, items)
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

func (s *Server) pluginOutputReview(w http.ResponseWriter, r *http.Request) {
	review, err := s.store.GetPluginOutputReview(r.Context(), r.PathValue("taskID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, review)
}

func (s *Server) updatePluginOutputReview(w http.ResponseWriter, r *http.Request) {
	var input struct {
		Disposition *string `json:"disposition"`
		Rank        *string `json:"rank"`
		Notes       *string `json:"notes"`
	}
	if err := decodeJSON(w, r, &input); err != nil {
		return
	}
	review, err := s.store.UpdatePluginOutputReview(r.Context(), r.PathValue("taskID"), store.PluginOutputReviewUpdate{
		Disposition: input.Disposition, Rank: input.Rank, Notes: input.Notes,
	})
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, review)
}

func (s *Server) pluginOutputReviewHistory(w http.ResponseWriter, r *http.Request) {
	events, err := s.store.ListPluginOutputReviewEvents(r.Context(), r.PathValue("taskID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, events)
}

func (s *Server) listURLs(w http.ResponseWriter, r *http.Request) {
	items, err := s.store.ListTargetURLs(r.Context(), r.PathValue("targetID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, items)
}

func (s *Server) searchURLs(w http.ResponseWriter, r *http.Request) {
	filter, err := urlFilter(r)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	result, err := s.store.SearchURLs(r.Context(), r.PathValue("targetID"), filter)
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, result)
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
	items, err := s.store.ListTransactions(r.Context(), sessionID, r.URL.Query().Get("target_id"))
	if err != nil {
		s.internalError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, items)
}

func (s *Server) searchTransactions(w http.ResponseWriter, r *http.Request) {
	filter, err := transactionFilter(r, true)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	sessionID := r.URL.Query().Get("session_id")
	if sessionID == "" {
		writeError(w, http.StatusBadRequest, "session_id is required")
		return
	}
	result, err := s.store.SearchTransactions(r.Context(), sessionID, r.URL.Query().Get("target_id"), filter)
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, result)
}

func (s *Server) listTargetTransactions(w http.ResponseWriter, r *http.Request) {
	items, err := s.store.ListTargetTransactions(r.Context(), r.PathValue("targetID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, items)
}

func (s *Server) searchTargetTransactions(w http.ResponseWriter, r *http.Request) {
	filter, err := transactionFilter(r, false)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	result, err := s.store.SearchTransactions(r.Context(), "", r.PathValue("targetID"), filter)
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, result)
}

const maxHARBytes = 64 << 20

func (s *Server) importTransactions(w http.ResponseWriter, r *http.Request) {
	targetID := r.PathValue("targetID")
	if _, err := s.store.GetTarget(r.Context(), targetID); s.handleStoreError(w, err) {
		return
	}
	data, filename, err := readHARUpload(w, r)
	if err != nil {
		var tooLarge *http.MaxBytesError
		if errors.As(err, &tooLarge) || errors.Is(err, errHARTooLarge) {
			writeError(w, http.StatusRequestEntityTooLarge, "HAR exceeds 64 MiB")
		} else {
			writeError(w, http.StatusBadRequest, err.Error())
		}
		return
	}
	parsed, err := har.Parse(bytes.NewReader(data))
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	now := time.Now().UTC()
	storedSource, err := s.artifacts.Put(data)
	if err != nil {
		s.internalError(w, err)
		return
	}
	source := model.Artifact{
		ID: store.NewID("art"), TargetID: targetID, Name: safeUploadName(filename), MediaType: "application/json",
		Size: storedSource.Size, SHA256: storedSource.SHA256, Path: storedSource.Path, CreatedAt: now,
	}
	artifacts := []model.Artifact{source}
	transactions := make([]model.Transaction, 0, len(parsed))
	for index, item := range parsed {
		transaction := model.Transaction{
			ID: store.NewID("txn"), TargetID: targetID, Method: item.Method, URL: item.URL,
			RequestHeaders: item.RequestHeaders, StatusCode: item.StatusCode, ResponseHeaders: item.ResponseHeaders,
			SourceArtifactID: source.ID, DurationMS: item.DurationMS, CreatedAt: item.StartedAt,
		}
		if len(item.RequestBody) != 0 {
			body, putErr := s.artifacts.Put(item.RequestBody)
			if putErr != nil {
				s.internalError(w, putErr)
				return
			}
			artifact := model.Artifact{
				ID: store.NewID("art"), TargetID: targetID,
				Name: fmt.Sprintf("transaction-%06d-request-body", index+1), MediaType: mediaTypeOrDefault(item.RequestMediaType),
				Size: body.Size, SHA256: body.SHA256, Path: body.Path, CreatedAt: item.StartedAt,
			}
			artifacts = append(artifacts, artifact)
			transaction.RequestBodyArtifactID = artifact.ID
		}
		if len(item.ResponseBody) != 0 {
			body, putErr := s.artifacts.Put(item.ResponseBody)
			if putErr != nil {
				s.internalError(w, putErr)
				return
			}
			artifact := model.Artifact{
				ID: store.NewID("art"), TargetID: targetID,
				Name: fmt.Sprintf("transaction-%06d-response-body", index+1), MediaType: mediaTypeOrDefault(item.ResponseMediaType),
				Size: body.Size, SHA256: body.SHA256, Path: body.Path, CreatedAt: item.StartedAt,
			}
			artifacts = append(artifacts, artifact)
			transaction.ResponseBodyArtifactID = artifact.ID
		}
		transactions = append(transactions, transaction)
	}
	if err := s.store.ImportTransactions(r.Context(), targetID, artifacts, transactions); s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusCreated, map[string]any{
		"imported": len(transactions), "source_artifact": source, "transactions": transactions,
	})
}

var errHARTooLarge = errors.New("HAR is too large")

func readHARUpload(w http.ResponseWriter, r *http.Request) ([]byte, string, error) {
	r.Body = http.MaxBytesReader(w, r.Body, maxHARBytes+(1<<20))
	reader, err := r.MultipartReader()
	if err != nil {
		return nil, "", errors.New("multipart form with a har file is required")
	}
	var data []byte
	var filename string
	for {
		part, nextErr := reader.NextPart()
		if errors.Is(nextErr, io.EOF) {
			break
		}
		if nextErr != nil {
			return nil, "", nextErr
		}
		if part.FormName() != "har" || part.FileName() == "" {
			_, _ = io.Copy(io.Discard, part)
			part.Close()
			continue
		}
		if data != nil {
			part.Close()
			return nil, "", errors.New("only one har file may be imported")
		}
		data, err = io.ReadAll(io.LimitReader(part, maxHARBytes+1))
		filename = part.FileName()
		part.Close()
		if err != nil {
			return nil, "", fmt.Errorf("read HAR: %w", err)
		}
		if len(data) > maxHARBytes {
			return nil, "", errHARTooLarge
		}
	}
	if data == nil {
		return nil, "", errors.New("multipart field har is required")
	}
	return data, filename, nil
}

func safeUploadName(name string) string {
	name = path.Base(strings.ReplaceAll(name, `\`, "/"))
	if name == "." || name == "/" || name == "" {
		return "capture.har"
	}
	return name
}

func mediaTypeOrDefault(value string) string {
	if value == "" {
		return "application/octet-stream"
	}
	return value
}

func (s *Server) getTransaction(w http.ResponseWriter, r *http.Request) {
	item, err := s.store.GetTransaction(r.Context(), r.PathValue("targetID"), r.PathValue("transactionID"))
	if s.handleStoreError(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, item)
}

func (s *Server) deleteTransaction(w http.ResponseWriter, r *http.Request) {
	if s.handleStoreError(w, s.store.DeleteTransaction(r.Context(), r.PathValue("targetID"), r.PathValue("transactionID"))) {
		return
	}
	w.WriteHeader(http.StatusNoContent)
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
	if errors.Is(err, store.ErrConflict) {
		writeError(w, http.StatusConflict, err.Error())
		return true
	}
	if errors.Is(err, store.ErrInvalid) {
		writeError(w, http.StatusBadRequest, err.Error())
		return true
	}
	s.internalError(w, err)
	return true
}

func targetFilter(r *http.Request) (store.TargetFilter, error) {
	query := r.URL.Query()
	for key := range query {
		switch key {
		case "search", "kind", "scope", "limit", "offset":
		default:
			return store.TargetFilter{}, fmt.Errorf("unknown query parameter %q", key)
		}
		if len(query[key]) != 1 {
			return store.TargetFilter{}, fmt.Errorf("query parameter %q must appear once", key)
		}
	}
	filter := store.TargetFilter{
		Search: strings.TrimSpace(query.Get("search")),
		Kind:   strings.TrimSpace(query.Get("kind")),
		Limit:  100,
	}
	if len(filter.Search) > 512 {
		return store.TargetFilter{}, errors.New("search must not exceed 512 characters")
	}
	if filter.Kind != "" && filter.Kind != "url" && filter.Kind != "hostname" && filter.Kind != "ip" && filter.Kind != "cidr" {
		return store.TargetFilter{}, errors.New("kind must be url, hostname, ip, or cidr")
	}
	var err error
	if filter.Scope, err = optionalBoolean("scope", query.Get("scope")); err != nil {
		return store.TargetFilter{}, err
	}
	if value := query.Get("limit"); value != "" {
		filter.Limit, err = strconv.Atoi(value)
		if err != nil || filter.Limit < 1 || filter.Limit > 1000 {
			return store.TargetFilter{}, errors.New("limit must be between 1 and 1000")
		}
	}
	if value := query.Get("offset"); value != "" {
		filter.Offset, err = strconv.Atoi(value)
		if err != nil || filter.Offset < 0 {
			return store.TargetFilter{}, errors.New("offset must be zero or greater")
		}
	}
	return filter, nil
}

func urlFilter(r *http.Request) (store.URLFilter, error) {
	query := r.URL.Query()
	for key := range query {
		switch key {
		case "search", "visited", "scope", "limit", "offset":
		default:
			return store.URLFilter{}, fmt.Errorf("unknown query parameter %q", key)
		}
		if len(query[key]) != 1 {
			return store.URLFilter{}, fmt.Errorf("query parameter %q must appear once", key)
		}
	}
	filter := store.URLFilter{Search: strings.TrimSpace(query.Get("search")), Limit: 100}
	if len(filter.Search) > 512 {
		return store.URLFilter{}, errors.New("search must not exceed 512 characters")
	}
	var err error
	if filter.Visited, err = optionalBoolean("visited", query.Get("visited")); err != nil {
		return store.URLFilter{}, err
	}
	if filter.Scope, err = optionalBoolean("scope", query.Get("scope")); err != nil {
		return store.URLFilter{}, err
	}
	if value := query.Get("limit"); value != "" {
		filter.Limit, err = strconv.Atoi(value)
		if err != nil || filter.Limit < 1 || filter.Limit > 1000 {
			return store.URLFilter{}, errors.New("limit must be between 1 and 1000")
		}
	}
	if value := query.Get("offset"); value != "" {
		filter.Offset, err = strconv.Atoi(value)
		if err != nil || filter.Offset < 0 {
			return store.URLFilter{}, errors.New("offset must be zero or greater")
		}
	}
	return filter, nil
}

func optionalBoolean(name, value string) (*bool, error) {
	if value == "" {
		return nil, nil
	}
	if value != "true" && value != "false" {
		return nil, fmt.Errorf("%s must be true or false", name)
	}
	parsed := value == "true"
	return &parsed, nil
}

func transactionFilter(r *http.Request, ownership bool) (store.TransactionFilter, error) {
	query := r.URL.Query()
	for key := range query {
		allowed := key == "search" || key == "method" || key == "status_code" || key == "limit" || key == "offset"
		allowed = allowed || (ownership && (key == "session_id" || key == "target_id"))
		if !allowed {
			return store.TransactionFilter{}, fmt.Errorf("unknown query parameter %q", key)
		}
		if len(query[key]) != 1 {
			return store.TransactionFilter{}, fmt.Errorf("query parameter %q must appear once", key)
		}
	}
	filter := store.TransactionFilter{
		Search: strings.TrimSpace(query.Get("search")),
		Method: strings.ToUpper(strings.TrimSpace(query.Get("method"))),
		Limit:  100,
	}
	if len(filter.Search) > 512 {
		return store.TransactionFilter{}, errors.New("search must not exceed 512 characters")
	}
	if len(filter.Method) > 32 {
		return store.TransactionFilter{}, errors.New("method must not exceed 32 characters")
	}
	for _, char := range filter.Method {
		if char < 'A' || char > 'Z' {
			return store.TransactionFilter{}, errors.New("method must contain only ASCII letters")
		}
	}
	if value := query.Get("status_code"); value != "" {
		statusCode, err := strconv.Atoi(value)
		if err != nil || statusCode < 100 || statusCode > 999 {
			return store.TransactionFilter{}, errors.New("status_code must be between 100 and 999")
		}
		filter.StatusCode = &statusCode
	}
	var err error
	if value := query.Get("limit"); value != "" {
		filter.Limit, err = strconv.Atoi(value)
		if err != nil || filter.Limit < 1 || filter.Limit > 1000 {
			return store.TransactionFilter{}, errors.New("limit must be between 1 and 1000")
		}
	}
	if value := query.Get("offset"); value != "" {
		filter.Offset, err = strconv.Atoi(value)
		if err != nil || filter.Offset < 0 {
			return store.TransactionFilter{}, errors.New("offset must be zero or greater")
		}
	}
	return filter, nil
}

func (s *Server) internalError(w http.ResponseWriter, err error) {
	slog.Error("api request failed", "error", err)
	writeError(w, http.StatusInternalServerError, "internal server error")
}

func decodeJSON(w http.ResponseWriter, r *http.Request, destination any) error {
	decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
	decoder.DisallowUnknownFields()
	decoder.UseNumber()
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
