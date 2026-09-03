package runner

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"strings"
	"sync"
	"time"

	"github.com/owtf/owtf/internal/artifact"
	"github.com/owtf/owtf/internal/model"
	"github.com/owtf/owtf/internal/plugin"
	"github.com/owtf/owtf/internal/store"
)

// Runner coordinates a bounded set of workers over durable task records.
type Runner struct {
	store     *store.Store
	artifacts *artifact.Store
	catalog   *plugin.Catalog
	workers   int
	timeout   time.Duration
	queue     chan string
	cancel    context.CancelFunc
	wg        sync.WaitGroup
	mu        sync.RWMutex
	state     []model.Worker
	cancels   map[string]context.CancelFunc
}

// New creates a runner with a fixed worker count and per-task timeout.
func New(database *store.Store, artifacts *artifact.Store, catalog *plugin.Catalog, workers int, timeout time.Duration) *Runner {
	if workers < 1 {
		workers = 1
	}
	if timeout <= 0 {
		timeout = 30 * time.Second
	}
	runner := &Runner{
		store: database, artifacts: artifacts, catalog: catalog,
		workers: workers, timeout: timeout, queue: make(chan string, 256), cancels: make(map[string]context.CancelFunc),
	}
	for index := 0; index < workers; index++ {
		runner.state = append(runner.state, model.Worker{ID: fmt.Sprintf("worker-%d", index+1), Status: "idle"})
	}
	return runner
}

// Start launches workers and requeues tasks interrupted by an earlier process.
func (r *Runner) Start(parent context.Context) error {
	ctx, cancel := context.WithCancel(parent)
	r.cancel = cancel
	for index := 0; index < r.workers; index++ {
		r.wg.Add(1)
		go r.worker(ctx, index)
	}
	recovered, err := r.store.RecoverTasks(ctx)
	if err != nil {
		cancel()
		r.wg.Wait()
		return fmt.Errorf("recover tasks: %w", err)
	}
	return r.Submit(ctx, recovered)
}

// Stop cancels active work and waits for every worker to exit.
func (r *Runner) Stop() {
	if r.cancel != nil {
		r.cancel()
	}
	r.wg.Wait()
	r.mu.Lock()
	for index := range r.state {
		r.state[index].Status = "stopped"
	}
	r.mu.Unlock()
}

// Workers returns a race-safe snapshot of current worker state.
func (r *Runner) Workers() []model.Worker {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return append([]model.Worker(nil), r.state...)
}

// Cancel records task cancellation and signals the active executor, if any.
func (r *Runner) Cancel(ctx context.Context, taskID string) (model.Task, error) {
	r.mu.RLock()
	cancel := r.cancels[taskID]
	r.mu.RUnlock()
	if cancel != nil {
		cancel()
	}
	return r.store.CancelTask(ctx, taskID)
}

// Submit places durable task IDs on the bounded in-memory dispatch queue.
func (r *Runner) Submit(ctx context.Context, taskIDs []string) error {
	for _, taskID := range taskIDs {
		select {
		case r.queue <- taskID:
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	return nil
}

func (r *Runner) worker(ctx context.Context, index int) {
	defer r.wg.Done()
	for {
		select {
		case taskID := <-r.queue:
			r.begin(index, taskID)
			outcome := r.execute(ctx, index, taskID)
			r.finish(index, outcome)
		case <-ctx.Done():
			return
		}
	}
}

func (r *Runner) execute(parent context.Context, workerIndex int, taskID string) string {
	taskCtx, taskCancel := context.WithCancel(parent)
	r.mu.Lock()
	r.cancels[taskID] = taskCancel
	r.mu.Unlock()
	defer taskCancel()
	defer func() {
		r.mu.Lock()
		delete(r.cancels, taskID)
		r.mu.Unlock()
	}()

	execution, err := r.store.StartTask(parent, taskID)
	if err != nil {
		if parent.Err() == nil && taskCtx.Err() == nil && !errors.Is(err, store.ErrTaskNotRunning) {
			slog.Error("start task", "task_id", taskID, "error", err)
		}
		return ""
	}
	r.assign(workerIndex, execution)
	logEvent := func(stream, message string) {
		message = strings.TrimSpace(message)
		if message == "" {
			return
		}
		if err := r.store.AddTaskEvent(parent, execution.ID, execution.AttemptID, stream, message); err != nil && parent.Err() == nil {
			slog.Error("record task event", "task_id", execution.ID, "error", err)
		}
	}
	logEvent("system", "task started")

	entry, ok := r.catalog.Get(execution.PluginID)
	if !ok {
		r.fail(parent, execution, logEvent, fmt.Errorf("plugin %s is not in the catalog", execution.PluginID))
		return model.TaskFailed
	}
	if entry.Availability != "ready" || entry.Executor == nil {
		r.fail(parent, execution, logEvent, fmt.Errorf("plugin %s is unavailable: %s", execution.PluginID, entry.Reason))
		return model.TaskFailed
	}

	ctx, cancel := context.WithTimeout(taskCtx, r.timeout)
	defer cancel()
	result, err := entry.Executor(ctx, plugin.Request{
		TaskID: execution.ID, PluginID: execution.PluginID, Target: execution.Target, Log: logEvent,
	})
	if err != nil {
		if errors.Is(ctx.Err(), context.Canceled) && parent.Err() == nil {
			logEvent("system", "task cancelled")
			_, _ = r.store.CancelTask(parent, execution.ID)
			return model.TaskCancelled
		}
		r.fail(parent, execution, logEvent, err)
		return model.TaskFailed
	}

	artifacts, artifactIDs, err := r.persistArtifacts(execution, result.Artifacts)
	if err != nil {
		r.fail(parent, execution, logEvent, err)
		return model.TaskFailed
	}
	now := time.Now().UTC()
	transactions := make([]model.Transaction, 0, len(result.Transactions))
	for _, item := range result.Transactions {
		artifactID := ""
		if item.ResponseBodyArtifactName != "" {
			var found bool
			artifactID, found = artifactIDs[item.ResponseBodyArtifactName]
			if !found {
				r.fail(parent, execution, logEvent, fmt.Errorf("exchange references unknown artifact %q", item.ResponseBodyArtifactName))
				return model.TaskFailed
			}
		}
		transactions = append(transactions, model.Transaction{
			ID: store.NewID("txn"), TaskID: execution.ID, TargetID: execution.TargetID,
			Method: item.Method, URL: item.URL, RequestHeaders: item.RequestHeaders,
			StatusCode: item.StatusCode, ResponseHeaders: item.ResponseHeaders,
			ResponseBodyArtifactID: artifactID, DurationMS: item.DurationMS, CreatedAt: now,
		})
	}
	observations := make([]model.Observation, 0, len(result.Observations))
	for _, item := range result.Observations {
		observations = append(observations, model.Observation{
			ID: store.NewID("obs"), TaskID: execution.ID, TargetID: execution.TargetID,
			TechniqueCode: item.TechniqueCode, Kind: item.Kind, Data: item.Data, CreatedAt: now,
		})
	}
	findings := make([]model.Finding, 0, len(result.Findings))
	for _, item := range result.Findings {
		findings = append(findings, model.Finding{
			ID: store.NewID("fnd"), TaskID: execution.ID, TargetID: execution.TargetID,
			TechniqueCode: item.TechniqueCode, Title: item.Title, Severity: item.Severity,
			Description: item.Description, CreatedAt: now,
		})
	}
	if err := r.store.CompleteTask(parent, execution, artifacts, transactions, observations, findings); err != nil {
		if errors.Is(err, store.ErrTaskNotRunning) {
			return model.TaskCancelled
		}
		r.fail(parent, execution, logEvent, fmt.Errorf("persist plugin result: %w", err))
		return model.TaskFailed
	}
	logEvent("system", "task completed")
	return model.TaskSucceeded
}

func (r *Runner) begin(index int, taskID string) {
	now := time.Now().UTC()
	r.mu.Lock()
	r.state[index].Status = "starting"
	r.state[index].TaskID = taskID
	r.state[index].TaskStartedAt = &now
	r.mu.Unlock()
}

func (r *Runner) assign(index int, execution model.TaskExecution) {
	r.mu.Lock()
	r.state[index].Status = "running"
	r.state[index].TaskID = execution.ID
	r.state[index].TargetID = execution.TargetID
	r.state[index].PluginID = execution.PluginID
	r.mu.Unlock()
}

func (r *Runner) finish(index int, outcome string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	switch outcome {
	case model.TaskSucceeded:
		r.state[index].Completed++
	case model.TaskFailed:
		r.state[index].Failed++
	case model.TaskCancelled:
		r.state[index].Cancelled++
	}
	r.state[index].Status = "idle"
	r.state[index].TaskID = ""
	r.state[index].TargetID = ""
	r.state[index].PluginID = ""
	r.state[index].TaskStartedAt = nil
}

func (r *Runner) persistArtifacts(execution model.TaskExecution, results []plugin.ArtifactResult) ([]model.Artifact, map[string]string, error) {
	items := make([]model.Artifact, 0, len(results))
	ids := make(map[string]string, len(results))
	for _, result := range results {
		if strings.TrimSpace(result.Name) == "" {
			return nil, nil, fmt.Errorf("plugin returned an artifact without a name")
		}
		if _, exists := ids[result.Name]; exists {
			return nil, nil, fmt.Errorf("plugin returned duplicate artifact name %q", result.Name)
		}
		stored, err := r.artifacts.Put(result.Data)
		if err != nil {
			return nil, nil, err
		}
		mediaType := result.MediaType
		if mediaType == "" {
			mediaType = "application/octet-stream"
		}
		id := store.NewID("art")
		ids[result.Name] = id
		items = append(items, model.Artifact{
			ID: id, TaskID: execution.ID, TargetID: execution.TargetID, Name: result.Name, MediaType: mediaType,
			Size: stored.Size, SHA256: stored.SHA256, Path: stored.Path, CreatedAt: time.Now().UTC(),
		})
	}
	return items, ids, nil
}

func (r *Runner) fail(ctx context.Context, execution model.TaskExecution, logEvent func(string, string), taskError error) {
	logEvent("stderr", taskError.Error())
	if err := r.store.FailTask(ctx, execution, taskError); err != nil && ctx.Err() == nil {
		slog.Error("fail task", "task_id", execution.ID, "error", err)
	}
}
