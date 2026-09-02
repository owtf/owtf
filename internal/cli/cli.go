package cli

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/owtf/owtf/internal/domain"
	targetvalue "github.com/owtf/owtf/internal/target"
)

const defaultURL = "http://127.0.0.1:8009"

type app struct {
	baseURL *url.URL
	client  *http.Client
	out     io.Writer
	errOut  io.Writer
}

type stringList []string

func (values *stringList) String() string { return strings.Join(*values, ",") }

func (values *stringList) Set(value string) error {
	for _, item := range strings.Split(value, ",") {
		if item = strings.TrimSpace(item); item != "" {
			*values = append(*values, item)
		}
	}
	return nil
}

// Run parses and executes one CLI request against an OWTF server.
func Run(ctx context.Context, args []string, out, errOut io.Writer) error {
	flags := flag.NewFlagSet("owtf-next", flag.ContinueOnError)
	flags.SetOutput(errOut)
	baseURL := flags.String("url", env("OWTF_URL", defaultURL), "OWTF server URL")
	timeout := flags.Duration("timeout", 30*time.Second, "HTTP request timeout")
	flags.Usage = func() { printUsage(errOut) }
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() == 0 {
		printUsage(out)
		return nil
	}
	parsedURL, err := url.Parse(*baseURL)
	if err != nil || (parsedURL.Scheme != "http" && parsedURL.Scheme != "https") || parsedURL.Host == "" {
		return fmt.Errorf("invalid OWTF server URL %q", *baseURL)
	}
	parsedURL.Path = strings.TrimRight(parsedURL.Path, "/")
	application := &app{
		baseURL: parsedURL,
		client:  &http.Client{Timeout: *timeout},
		out:     out,
		errOut:  errOut,
	}
	command := flags.Arg(0)
	commandArgs := flags.Args()[1:]
	switch command {
	case "health":
		return application.proxyJSON(ctx, http.MethodGet, "/debug/health", nil)
	case "sessions":
		return application.sessions(ctx, commandArgs)
	case "targets":
		return application.targets(ctx, commandArgs)
	case "plugins":
		return application.plugins(ctx, commandArgs)
	case "runs":
		return application.runs(ctx, commandArgs)
	case "scan":
		return application.scan(ctx, commandArgs)
	case "worklist":
		return application.worklist(ctx, commandArgs)
	case "workers":
		return application.workers(ctx, commandArgs)
	case "tasks":
		return application.tasks(ctx, commandArgs)
	case "transactions":
		return application.transactions(ctx, commandArgs)
	case "artifacts":
		return application.artifacts(ctx, commandArgs)
	case "help":
		printUsage(out)
		return nil
	default:
		return fmt.Errorf("unknown command %q; run owtf-next help", command)
	}
}

func (a *app) sessions(ctx context.Context, args []string) error {
	if len(args) == 0 {
		return errors.New("sessions requires list, create, or show")
	}
	switch args[0] {
	case "list":
		return noArgs(args[1:], func() error {
			return a.proxyJSON(ctx, http.MethodGet, "/api/v2/sessions", nil)
		})
	case "create":
		flags := a.flags("sessions create")
		name := flags.String("name", "Default session", "session name")
		if err := flags.Parse(args[1:]); err != nil {
			return err
		}
		if flags.NArg() != 0 {
			return errors.New("sessions create accepts no positional arguments")
		}
		return a.proxyJSON(ctx, http.MethodPost, "/api/v2/sessions", map[string]any{"name": *name})
	case "show":
		id, err := oneArg("sessions show", args[1:])
		if err != nil {
			return err
		}
		return a.proxyJSON(ctx, http.MethodGet, "/api/v2/sessions/"+pathSegment(id), nil)
	default:
		return fmt.Errorf("unknown sessions command %q", args[0])
	}
}

func (a *app) targets(ctx context.Context, args []string) error {
	if len(args) == 0 {
		return errors.New("targets requires list, add, show, delete, or report")
	}
	switch args[0] {
	case "list":
		flags := a.flags("targets list")
		sessionID := flags.String("session", "", "session ID")
		if err := flags.Parse(args[1:]); err != nil {
			return err
		}
		if *sessionID == "" || flags.NArg() != 0 {
			return errors.New("usage: owtf-next targets list --session SESSION_ID")
		}
		return a.proxyJSON(ctx, http.MethodGet, "/api/v2/sessions/"+pathSegment(*sessionID)+"/targets", nil)
	case "add":
		flags := a.flags("targets add")
		sessionID := flags.String("session", "", "session ID")
		if err := flags.Parse(args[1:]); err != nil {
			return err
		}
		if *sessionID == "" || flags.NArg() == 0 {
			return errors.New("usage: owtf-next targets add --session SESSION_ID TARGET...")
		}
		return a.proxyJSON(ctx, http.MethodPost, "/api/v2/sessions/"+pathSegment(*sessionID)+"/targets", map[string]any{"targets": flags.Args()})
	case "show", "report":
		id, err := oneArg("targets "+args[0], args[1:])
		if err != nil {
			return err
		}
		path := "/api/v2/targets/" + pathSegment(id)
		if args[0] == "report" {
			path += "/report"
		}
		return a.proxyJSON(ctx, http.MethodGet, path, nil)
	case "delete":
		if len(args) < 2 {
			return errors.New("usage: owtf-next targets delete TARGET_ID...")
		}
		deleted := make([]string, 0, len(args)-1)
		for _, id := range args[1:] {
			if err := a.request(ctx, http.MethodDelete, "/api/v2/targets/"+pathSegment(id), nil, nil); err != nil {
				return err
			}
			deleted = append(deleted, id)
		}
		return a.writeJSON(map[string]any{"deleted": deleted})
	default:
		return fmt.Errorf("unknown targets command %q", args[0])
	}
}

func (a *app) plugins(ctx context.Context, args []string) error {
	if len(args) != 1 || args[0] != "list" {
		return errors.New("usage: owtf-next plugins list")
	}
	return a.proxyJSON(ctx, http.MethodGet, "/api/v2/plugins", nil)
}

func (a *app) runs(ctx context.Context, args []string) error {
	if len(args) == 0 || args[0] != "create" {
		return errors.New("usage: owtf-next runs create --session SESSION_ID --target TARGET_ID --plugin PLUGIN_ID")
	}
	flags := a.flags("runs create")
	sessionID := flags.String("session", "", "session ID")
	var targetIDs, pluginIDs stringList
	flags.Var(&targetIDs, "target", "target ID (repeatable or comma-separated)")
	flags.Var(&pluginIDs, "plugin", "plugin ID (repeatable or comma-separated)")
	if err := flags.Parse(args[1:]); err != nil {
		return err
	}
	if *sessionID == "" || len(targetIDs) == 0 || len(pluginIDs) == 0 || flags.NArg() != 0 {
		return errors.New("usage: owtf-next runs create --session SESSION_ID --target TARGET_ID --plugin PLUGIN_ID")
	}
	return a.proxyJSON(ctx, http.MethodPost, "/api/v2/runs", map[string]any{
		"session_id": *sessionID,
		"target_ids": []string(targetIDs),
		"plugin_ids": []string(pluginIDs),
	})
}

func (a *app) scan(ctx context.Context, args []string) error {
	flags := a.flags("scan")
	sessionID := flags.String("session", "", "existing session ID; defaults to the newest session")
	var pluginIDs stringList
	flags.Var(&pluginIDs, "plugin", "plugin ID (repeatable or comma-separated)")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if len(pluginIDs) == 0 || flags.NArg() == 0 {
		return errors.New("usage: owtf-next scan [--session SESSION_ID] --plugin PLUGIN_ID TARGET...")
	}
	resolvedSessionID, err := a.ensureSession(ctx, *sessionID)
	if err != nil {
		return err
	}
	var added struct {
		Created []domain.Target `json:"created"`
		Invalid []struct {
			Input string `json:"input"`
			Error string `json:"error"`
		} `json:"invalid"`
	}
	path := "/api/v2/sessions/" + pathSegment(resolvedSessionID) + "/targets"
	if err := a.request(ctx, http.MethodPost, path, map[string]any{"targets": flags.Args()}, &added); err != nil {
		return err
	}
	if len(added.Invalid) > 0 {
		return fmt.Errorf("invalid target %q: %s", added.Invalid[0].Input, added.Invalid[0].Error)
	}
	targetIDs, err := a.resolveTargetIDs(ctx, resolvedSessionID, flags.Args())
	if err != nil {
		return err
	}
	var result any
	if err := a.request(ctx, http.MethodPost, "/api/v2/runs", map[string]any{
		"session_id": resolvedSessionID,
		"target_ids": targetIDs,
		"plugin_ids": []string(pluginIDs),
	}, &result); err != nil {
		return err
	}
	return a.writeJSON(result)
}

func (a *app) ensureSession(ctx context.Context, id string) (string, error) {
	if id != "" {
		return id, nil
	}
	var sessions []domain.Session
	if err := a.request(ctx, http.MethodGet, "/api/v2/sessions", nil, &sessions); err != nil {
		return "", err
	}
	if len(sessions) > 0 {
		return sessions[0].ID, nil
	}
	var session domain.Session
	if err := a.request(ctx, http.MethodPost, "/api/v2/sessions", map[string]any{"name": "Default session"}, &session); err != nil {
		return "", err
	}
	return session.ID, nil
}

func (a *app) resolveTargetIDs(ctx context.Context, sessionID string, inputs []string) ([]string, error) {
	wanted := make(map[string]bool, len(inputs))
	for _, input := range inputs {
		normalized, err := targetvalue.Normalize(input)
		if err != nil {
			return nil, err
		}
		wanted[normalized.Value] = true
	}
	var targets []domain.Target
	path := "/api/v2/sessions/" + pathSegment(sessionID) + "/targets"
	if err := a.request(ctx, http.MethodGet, path, nil, &targets); err != nil {
		return nil, err
	}
	ids := make([]string, 0, len(wanted))
	for _, target := range targets {
		if wanted[target.Value] {
			ids = append(ids, target.ID)
			delete(wanted, target.Value)
		}
	}
	if len(wanted) != 0 {
		return nil, errors.New("server did not retain every target")
	}
	return ids, nil
}

func (a *app) worklist(ctx context.Context, args []string) error {
	flags := a.flags("worklist")
	sessionID := flags.String("session", "", "session ID")
	status := flags.String("status", "", "task status")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("worklist accepts only flags")
	}
	query := url.Values{}
	if *sessionID != "" {
		query.Set("session_id", *sessionID)
	}
	if *status != "" {
		query.Set("status", *status)
	}
	return a.proxyJSON(ctx, http.MethodGet, withQuery("/api/v2/tasks", query), nil)
}

func (a *app) workers(ctx context.Context, args []string) error {
	return noArgs(args, func() error {
		return a.proxyJSON(ctx, http.MethodGet, "/api/v2/workers", nil)
	})
}

func (a *app) tasks(ctx context.Context, args []string) error {
	if len(args) == 0 {
		return errors.New("tasks requires show, logs, or cancel")
	}
	id, err := oneArg("tasks "+args[0], args[1:])
	if err != nil {
		return err
	}
	path := "/api/v2/tasks/" + pathSegment(id)
	switch args[0] {
	case "show":
		return a.proxyJSON(ctx, http.MethodGet, path, nil)
	case "logs":
		return a.proxyJSON(ctx, http.MethodGet, path+"/events", nil)
	case "cancel":
		return a.proxyJSON(ctx, http.MethodPost, path+"/cancel", map[string]any{})
	default:
		return fmt.Errorf("unknown tasks command %q", args[0])
	}
}

func (a *app) transactions(ctx context.Context, args []string) error {
	if len(args) == 0 || args[0] != "list" {
		return errors.New("usage: owtf-next transactions list --session SESSION_ID [--target TARGET_ID]")
	}
	flags := a.flags("transactions list")
	sessionID := flags.String("session", "", "session ID")
	targetID := flags.String("target", "", "target ID")
	if err := flags.Parse(args[1:]); err != nil {
		return err
	}
	if *sessionID == "" || flags.NArg() != 0 {
		return errors.New("usage: owtf-next transactions list --session SESSION_ID [--target TARGET_ID]")
	}
	query := url.Values{"session_id": {*sessionID}}
	if *targetID != "" {
		query.Set("target_id", *targetID)
	}
	return a.proxyJSON(ctx, http.MethodGet, withQuery("/api/v2/transactions", query), nil)
}

func (a *app) artifacts(ctx context.Context, args []string) error {
	if len(args) == 0 || args[0] != "get" {
		return errors.New("usage: owtf-next artifacts get [--output FILE] ARTIFACT_ID")
	}
	flags := a.flags("artifacts get")
	output := flags.String("output", "", "write artifact to this file instead of stdout")
	if err := flags.Parse(args[1:]); err != nil {
		return err
	}
	id, err := oneArg("artifacts get", flags.Args())
	if err != nil {
		return err
	}
	response, err := a.do(ctx, http.MethodGet, "/api/v2/artifacts/"+pathSegment(id), nil)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	if *output == "" {
		_, err = io.Copy(a.out, response.Body)
		return err
	}
	if err := os.MkdirAll(filepath.Dir(*output), 0o750); err != nil && filepath.Dir(*output) != "." {
		return err
	}
	file, err := os.Create(*output)
	if err != nil {
		return err
	}
	_, copyErr := io.Copy(file, response.Body)
	closeErr := file.Close()
	if copyErr != nil {
		return copyErr
	}
	return closeErr
}

func (a *app) flags(name string) *flag.FlagSet {
	flags := flag.NewFlagSet(name, flag.ContinueOnError)
	flags.SetOutput(a.errOut)
	return flags
}

func (a *app) proxyJSON(ctx context.Context, method, path string, body any) error {
	var value any
	if err := a.request(ctx, method, path, body, &value); err != nil {
		return err
	}
	return a.writeJSON(value)
}

func (a *app) request(ctx context.Context, method, path string, body, destination any) error {
	response, err := a.do(ctx, method, path, body)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	if destination == nil || response.StatusCode == http.StatusNoContent {
		_, _ = io.Copy(io.Discard, response.Body)
		return nil
	}
	decoder := json.NewDecoder(io.LimitReader(response.Body, 16<<20))
	if err := decoder.Decode(destination); err != nil {
		return fmt.Errorf("decode %s %s response: %w", method, path, err)
	}
	return nil
}

func (a *app) do(ctx context.Context, method, path string, body any) (*http.Response, error) {
	var reader io.Reader
	if body != nil {
		encoded, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		reader = bytes.NewReader(encoded)
	}
	endpoint := *a.baseURL
	endpoint.Path = strings.TrimRight(a.baseURL.Path, "/") + path
	endpoint.RawQuery = ""
	if index := strings.IndexByte(path, '?'); index >= 0 {
		endpoint.Path = strings.TrimRight(a.baseURL.Path, "/") + path[:index]
		endpoint.RawQuery = path[index+1:]
	}
	request, err := http.NewRequestWithContext(ctx, method, endpoint.String(), reader)
	if err != nil {
		return nil, err
	}
	request.Header.Set("Accept", "application/json")
	if body != nil {
		request.Header.Set("Content-Type", "application/json")
	}
	response, err := a.client.Do(request)
	if err != nil {
		return nil, fmt.Errorf("%s %s: %w", method, endpoint.String(), err)
	}
	if response.StatusCode >= 200 && response.StatusCode < 300 {
		return response, nil
	}
	defer response.Body.Close()
	data, _ := io.ReadAll(io.LimitReader(response.Body, 1<<20))
	var apiError struct {
		Error string `json:"error"`
	}
	if json.Unmarshal(data, &apiError) == nil && apiError.Error != "" {
		return nil, fmt.Errorf("%s %s: %s", method, path, apiError.Error)
	}
	return nil, fmt.Errorf("%s %s: server returned %s", method, path, response.Status)
}

func (a *app) writeJSON(value any) error {
	encoder := json.NewEncoder(a.out)
	encoder.SetIndent("", "  ")
	return encoder.Encode(value)
}

func pathSegment(value string) string { return url.PathEscape(value) }

func withQuery(path string, values url.Values) string {
	if len(values) == 0 {
		return path
	}
	return path + "?" + values.Encode()
}

func oneArg(command string, args []string) (string, error) {
	if len(args) != 1 || strings.TrimSpace(args[0]) == "" {
		return "", fmt.Errorf("%s requires exactly one ID", command)
	}
	return args[0], nil
}

func noArgs(args []string, run func() error) error {
	if len(args) != 0 {
		return errors.New("command accepts no arguments")
	}
	return run()
}

func env(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func printUsage(output io.Writer) {
	fmt.Fprint(output, `OWTF Next

Usage:
  owtf-next serve
  owtf-next [--url URL] health
  owtf-next [--url URL] sessions list|create|show
  owtf-next [--url URL] targets list|add|show|delete|report
  owtf-next [--url URL] plugins list
  owtf-next [--url URL] runs create --session ID --target ID --plugin ID
  owtf-next [--url URL] scan [--session ID] --plugin ID TARGET...
  owtf-next [--url URL] worklist [--session ID] [--status STATUS]
  owtf-next [--url URL] workers
  owtf-next [--url URL] tasks show|logs|cancel ID
  owtf-next [--url URL] transactions list --session ID [--target ID]
  owtf-next [--url URL] artifacts get [--output FILE] ID

Repeat --target and --plugin, or pass comma-separated IDs.
`)
}
