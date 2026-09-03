package cli

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/owtf/owtf/internal/model"
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
	flags := flag.NewFlagSet("owtf", flag.ContinueOnError)
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
		return fmt.Errorf("unknown command %q; run owtf help", command)
	}
}

func (a *app) sessions(ctx context.Context, args []string) error {
	if len(args) == 0 {
		return errors.New("sessions requires list, create, show, report, or export")
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
	case "show", "report":
		id, err := oneArg("sessions "+args[0], args[1:])
		if err != nil {
			return err
		}
		path := "/api/v2/sessions/" + pathSegment(id)
		if args[0] == "report" {
			path += "/report"
		}
		return a.proxyJSON(ctx, http.MethodGet, path, nil)
	case "export":
		flags := a.flags("sessions export")
		output := flags.String("output", "", "output ZIP path; defaults to owtf-SESSION_ID.zip")
		if err := flags.Parse(args[1:]); err != nil {
			return err
		}
		id, err := oneArg("sessions export", flags.Args())
		if err != nil {
			return err
		}
		if *output == "" {
			*output = "owtf-" + id + ".zip"
		}
		response, err := a.do(ctx, http.MethodGet, "/api/v2/sessions/"+pathSegment(id)+"/export", nil)
		if err != nil {
			return err
		}
		defer response.Body.Close()
		written, err := writeResponseFile(response.Body, *output)
		if err != nil {
			return err
		}
		return a.writeJSON(map[string]any{"session_id": id, "output": *output, "bytes": written})
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
			return errors.New("usage: owtf targets list --session SESSION_ID")
		}
		return a.proxyJSON(ctx, http.MethodGet, "/api/v2/sessions/"+pathSegment(*sessionID)+"/targets", nil)
	case "add":
		flags := a.flags("targets add")
		sessionID := flags.String("session", "", "session ID")
		if err := flags.Parse(args[1:]); err != nil {
			return err
		}
		if *sessionID == "" || flags.NArg() == 0 {
			return errors.New("usage: owtf targets add --session SESSION_ID TARGET...")
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
			return errors.New("usage: owtf targets delete TARGET_ID...")
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
	if len(args) == 0 || args[0] != "list" {
		return errors.New("usage: owtf plugins list [--group GROUP] [--type TYPE]")
	}
	flags := a.flags("plugins list")
	group := flags.String("group", "", "plugin group: web, network, or auxiliary")
	var pluginTypes stringList
	flags.Var(&pluginTypes, "type", "plugin type (repeatable or comma-separated)")
	if err := flags.Parse(args[1:]); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("usage: owtf plugins list [--group GROUP] [--type TYPE]")
	}
	query := url.Values{}
	if *group != "" {
		query.Set("group", *group)
	}
	for _, pluginType := range pluginTypes {
		query.Add("type", pluginType)
	}
	return a.proxyJSON(ctx, http.MethodGet, withQuery("/api/v2/plugins", query), nil)
}

func (a *app) runs(ctx context.Context, args []string) error {
	if len(args) == 0 {
		return errors.New("runs requires list, show, or create")
	}
	switch args[0] {
	case "list":
		flags := a.flags("runs list")
		sessionID := flags.String("session", "", "session ID")
		if err := flags.Parse(args[1:]); err != nil {
			return err
		}
		if *sessionID == "" || flags.NArg() != 0 {
			return errors.New("usage: owtf runs list --session SESSION_ID")
		}
		query := url.Values{"session_id": {*sessionID}}
		return a.proxyJSON(ctx, http.MethodGet, withQuery("/api/v2/runs", query), nil)
	case "show":
		id, err := oneArg("runs show", args[1:])
		if err != nil {
			return err
		}
		return a.proxyJSON(ctx, http.MethodGet, "/api/v2/runs/"+pathSegment(id), nil)
	case "create":
		flags := a.flags("runs create")
		sessionID := flags.String("session", "", "session ID")
		pluginGroup := flags.String("group", "", "plugin group: web, network, or auxiliary")
		var targetIDs, pluginIDs stringList
		var pluginTypes stringList
		flags.Var(&targetIDs, "target", "target ID (repeatable or comma-separated)")
		flags.Var(&pluginIDs, "plugin", "plugin ID (repeatable or comma-separated)")
		flags.Var(&pluginTypes, "type", "plugin type (repeatable or comma-separated)")
		if err := flags.Parse(args[1:]); err != nil {
			return err
		}
		if *sessionID == "" || len(targetIDs) == 0 || flags.NArg() != 0 {
			return errors.New("usage: owtf runs create --session ID --target ID (--plugin ID | --group GROUP [--type TYPE])")
		}
		selection, err := pluginSelection(pluginIDs, *pluginGroup, pluginTypes)
		if err != nil {
			return err
		}
		input := map[string]any{
			"session_id": *sessionID,
			"target_ids": []string(targetIDs),
		}
		for key, value := range selection {
			input[key] = value
		}
		return a.proxyJSON(ctx, http.MethodPost, "/api/v2/runs", input)
	default:
		return fmt.Errorf("unknown runs command %q", args[0])
	}
}

func (a *app) scan(ctx context.Context, args []string) error {
	flags := a.flags("scan")
	sessionID := flags.String("session", "", "existing session ID; defaults to the newest session")
	pluginGroup := flags.String("group", "", "plugin group: web, network, or auxiliary")
	var pluginIDs stringList
	var pluginTypes stringList
	flags.Var(&pluginIDs, "plugin", "plugin ID (repeatable or comma-separated)")
	flags.Var(&pluginTypes, "type", "plugin type (repeatable or comma-separated)")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() == 0 {
		return errors.New("usage: owtf scan [--session ID] (--plugin ID | --group GROUP [--type TYPE]) TARGET...")
	}
	selection, err := pluginSelection(pluginIDs, *pluginGroup, pluginTypes)
	if err != nil {
		return err
	}
	resolvedSessionID, err := a.ensureSession(ctx, *sessionID)
	if err != nil {
		return err
	}
	var added struct {
		Created []model.Target `json:"created"`
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
	input := map[string]any{
		"session_id": resolvedSessionID,
		"target_ids": targetIDs,
	}
	for key, value := range selection {
		input[key] = value
	}
	if err := a.request(ctx, http.MethodPost, "/api/v2/runs", input, &result); err != nil {
		return err
	}
	return a.writeJSON(result)
}

func pluginSelection(pluginIDs []string, group string, pluginTypes []string) (map[string]any, error) {
	if (len(pluginIDs) == 0 && group == "") || (len(pluginIDs) != 0 && group != "") {
		return nil, errors.New("select plugins with either --plugin or --group")
	}
	if group == "" && len(pluginTypes) != 0 {
		return nil, errors.New("--type requires --group")
	}
	if group != "" {
		return map[string]any{"plugin_group": group, "plugin_types": []string(pluginTypes)}, nil
	}
	return map[string]any{"plugin_ids": []string(pluginIDs)}, nil
}

func (a *app) ensureSession(ctx context.Context, id string) (string, error) {
	if id != "" {
		return id, nil
	}
	var sessions []model.Session
	if err := a.request(ctx, http.MethodGet, "/api/v2/sessions", nil, &sessions); err != nil {
		return "", err
	}
	if len(sessions) > 0 {
		return sessions[0].ID, nil
	}
	var session model.Session
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
	var targets []model.Target
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
	if len(args) == 0 {
		return errors.New("transactions requires list, show, delete, or import")
	}
	switch args[0] {
	case "list":
		flags := a.flags("transactions list")
		sessionID := flags.String("session", "", "session ID")
		targetID := flags.String("target", "", "target ID")
		if err := flags.Parse(args[1:]); err != nil {
			return err
		}
		if (*sessionID == "" && *targetID == "") || flags.NArg() != 0 {
			return errors.New("usage: owtf transactions list (--session SESSION_ID | --target TARGET_ID)")
		}
		if *sessionID == "" {
			return a.proxyJSON(ctx, http.MethodGet, "/api/v2/targets/"+pathSegment(*targetID)+"/transactions", nil)
		}
		query := url.Values{"session_id": {*sessionID}}
		if *targetID != "" {
			query.Set("target_id", *targetID)
		}
		return a.proxyJSON(ctx, http.MethodGet, withQuery("/api/v2/transactions", query), nil)
	case "show", "delete":
		flags := a.flags("transactions " + args[0])
		targetID := flags.String("target", "", "target ID")
		if err := flags.Parse(args[1:]); err != nil {
			return err
		}
		transactionID, err := oneArg("transactions "+args[0], flags.Args())
		if err != nil || *targetID == "" {
			return fmt.Errorf("usage: owtf transactions %s --target TARGET_ID TRANSACTION_ID", args[0])
		}
		path := "/api/v2/targets/" + pathSegment(*targetID) + "/transactions/" + pathSegment(transactionID)
		if args[0] == "show" {
			return a.proxyJSON(ctx, http.MethodGet, path, nil)
		}
		if err := a.request(ctx, http.MethodDelete, path, nil, nil); err != nil {
			return err
		}
		return a.writeJSON(map[string]string{"deleted": transactionID})
	case "import":
		flags := a.flags("transactions import")
		targetID := flags.String("target", "", "target ID")
		if err := flags.Parse(args[1:]); err != nil {
			return err
		}
		filename, err := oneArg("transactions import", flags.Args())
		if err != nil || *targetID == "" {
			return errors.New("usage: owtf transactions import --target TARGET_ID FILE.har")
		}
		return a.importTransactions(ctx, *targetID, filename)
	default:
		return fmt.Errorf("unknown transactions command %q", args[0])
	}
}

func (a *app) importTransactions(ctx context.Context, targetID, filename string) error {
	file, err := os.Open(filename)
	if err != nil {
		return fmt.Errorf("open HAR: %w", err)
	}
	defer file.Close()
	reader, writer := io.Pipe()
	multipartWriter := multipart.NewWriter(writer)
	contentType := multipartWriter.FormDataContentType()
	go func() {
		part, createErr := multipartWriter.CreateFormFile("har", filepath.Base(filename))
		if createErr == nil {
			_, createErr = io.Copy(part, file)
		}
		if closeErr := multipartWriter.Close(); createErr == nil {
			createErr = closeErr
		}
		_ = writer.CloseWithError(createErr)
	}()
	defer reader.Close()
	path := "/api/v2/targets/" + pathSegment(targetID) + "/transactions/import"
	response, err := a.send(ctx, http.MethodPost, path, reader, contentType)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	var result any
	if err := json.NewDecoder(io.LimitReader(response.Body, 16<<20)).Decode(&result); err != nil {
		return fmt.Errorf("decode transaction import response: %w", err)
	}
	return a.writeJSON(result)
}

func (a *app) artifacts(ctx context.Context, args []string) error {
	if len(args) == 0 || args[0] != "get" {
		return errors.New("usage: owtf artifacts get [--output FILE] ARTIFACT_ID")
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
	_, err = writeResponseFile(response.Body, *output)
	return err
}

func writeResponseFile(source io.Reader, output string) (int64, error) {
	directory := filepath.Dir(output)
	if err := os.MkdirAll(directory, 0o750); err != nil {
		return 0, fmt.Errorf("create output directory: %w", err)
	}
	temporary, err := os.CreateTemp(directory, "."+filepath.Base(output)+".tmp-*")
	if err != nil {
		return 0, fmt.Errorf("create temporary output: %w", err)
	}
	temporaryName := temporary.Name()
	defer os.Remove(temporaryName)
	written, copyErr := io.Copy(temporary, source)
	closeErr := temporary.Close()
	if copyErr != nil {
		return written, fmt.Errorf("write output: %w", copyErr)
	}
	if closeErr != nil {
		return written, fmt.Errorf("close output: %w", closeErr)
	}
	if err := os.Chmod(temporaryName, 0o640); err != nil {
		return written, fmt.Errorf("set output permissions: %w", err)
	}
	if err := os.Rename(temporaryName, output); err != nil {
		return written, fmt.Errorf("publish output: %w", err)
	}
	return written, nil
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
	contentType := ""
	if body != nil {
		encoded, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		reader = bytes.NewReader(encoded)
		contentType = "application/json"
	}
	return a.send(ctx, method, path, reader, contentType)
}

func (a *app) send(ctx context.Context, method, path string, body io.Reader, contentType string) (*http.Response, error) {
	endpoint := *a.baseURL
	endpoint.Path = strings.TrimRight(a.baseURL.Path, "/") + path
	endpoint.RawQuery = ""
	if index := strings.IndexByte(path, '?'); index >= 0 {
		endpoint.Path = strings.TrimRight(a.baseURL.Path, "/") + path[:index]
		endpoint.RawQuery = path[index+1:]
	}
	request, err := http.NewRequestWithContext(ctx, method, endpoint.String(), body)
	if err != nil {
		return nil, err
	}
	request.Header.Set("Accept", "application/json")
	if contentType != "" {
		request.Header.Set("Content-Type", contentType)
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
	fmt.Fprint(output, `OWTF

Usage:
  owtf serve [--config FILE] [--workers COUNT] [--task-timeout DURATION]
  owtf config show [--config FILE]
  owtf config validate FILE
  owtf proxy [--config FILE] [--listen ADDRESS] [--api-listen ADDRESS]
  owtf proxy status|transactions|transaction|stats|clear|ca|repeat
  owtf [--url URL] health
  owtf [--url URL] sessions list|create|show|report
  owtf [--url URL] sessions export [--output FILE] ID
  owtf [--url URL] targets list|add|show|delete|report
  owtf [--url URL] plugins list [--group GROUP] [--type TYPE]
  owtf [--url URL] runs list --session ID
  owtf [--url URL] runs show ID
  owtf [--url URL] runs create --session ID --target ID (--plugin ID | --group GROUP [--type TYPE])
  owtf [--url URL] scan [--session ID] (--plugin ID | --group GROUP [--type TYPE]) TARGET...
  owtf [--url URL] worklist [--session ID] [--status STATUS]
  owtf [--url URL] workers
  owtf [--url URL] tasks show|logs|cancel ID
  owtf [--url URL] transactions list (--session ID | --target ID)
  owtf [--url URL] transactions show|delete --target TARGET_ID TRANSACTION_ID
  owtf [--url URL] transactions import --target TARGET_ID FILE.har
  owtf [--url URL] artifacts get [--output FILE] ID

Repeat --target and --plugin, or pass comma-separated IDs.
`)
}
