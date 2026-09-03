package plugin

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/url"
	"regexp"
	"sort"
	"strings"

	"github.com/owtf/owtf/internal/model"
)

const (
	maxDecodedRecords = 10_000
	maxDecodedText    = 4 << 10
)

var artifactDecoders = map[string]func([]byte, decodeContext) (Result, error){
	"gobuster-dir":   decodeGobusterDir,
	"gobuster-gcs":   decodeGobusterGCS,
	"gobuster-vhost": decodeGobusterVHost,
	"nuclei-jsonl":   decodeNuclei,
	"testssl-json":   decodeTestSSL,
	"url-list":       decodeURLList,
	"wafw00f-json":   decodeWAFW00F,
	"wapiti-json":    decodeWapiti,
	"whatweb-json":   decodeWhatWeb,
}

type decodeContext struct {
	technique string
	target    model.Target
}

func validArtifactDecoder(name string) bool {
	_, ok := artifactDecoders[name]
	return ok
}

func decodeArtifacts(manifest Manifest, target model.Target, artifacts []ArtifactResult) (Result, error) {
	var artifactSpecs []CommandArtifact
	switch manifest.Spec.Runtime.Type {
	case "command":
		artifactSpecs = manifest.Spec.Runtime.Command.Artifacts
	case "container":
		artifactSpecs = manifest.Spec.Runtime.Container.Artifacts
	default:
		return Result{}, fmt.Errorf("runtime %q does not produce command artifacts", manifest.Spec.Runtime.Type)
	}
	specs := make(map[string]CommandArtifact, len(artifactSpecs))
	for _, spec := range artifactSpecs {
		specs[spec.Name] = spec
	}
	context := decodeContext{technique: manifest.Spec.Techniques[0].Code, target: target}
	var result Result
	for _, artifact := range artifacts {
		name := specs[artifact.Name].Decoder
		if name == "" {
			continue
		}
		decoded, err := artifactDecoders[name](artifact.Data, context)
		if err != nil {
			return Result{}, fmt.Errorf("decode artifact %s with %s: %w", artifact.Name, name, err)
		}
		result.URLs = append(result.URLs, decoded.URLs...)
		result.Observations = append(result.Observations, decoded.Observations...)
		result.Findings = append(result.Findings, decoded.Findings...)
	}
	return result, nil
}

func decodeTestSSL(data []byte, context decodeContext) (Result, error) {
	var rows []struct {
		ID       string `json:"id"`
		Severity string `json:"severity"`
		Finding  string `json:"finding"`
		CVE      string `json:"cve"`
		CWE      string `json:"cwe"`
	}
	if err := decodeJSON(data, &rows); err != nil {
		return Result{}, err
	}
	if len(rows) > maxDecodedRecords {
		return Result{}, fmt.Errorf("report has more than %d records", maxDecodedRecords)
	}
	var result Result
	for index, row := range rows {
		severity := strings.ToLower(strings.TrimSpace(row.Severity))
		if row.ID == "" || row.Finding == "" || severity == "" {
			return Result{}, fmt.Errorf("record %d is missing id, severity, or finding", index+1)
		}
		description := limited(row.Finding)
		if references := joinNonempty(row.CVE, row.CWE); references != "" {
			description += " (" + references + ")"
		}
		if isFindingSeverity(severity) {
			result.Findings = append(result.Findings, finding(context, "TLS: "+row.ID, severity, description))
			continue
		}
		result.Observations = append(result.Observations, observation(context, "tls.result", map[string]any{
			"id": row.ID, "severity": severity, "finding": description,
		}))
	}
	return result, nil
}

func decodeWAFW00F(data []byte, context decodeContext) (Result, error) {
	var rows []struct {
		URL          string `json:"url"`
		Detected     bool   `json:"detected"`
		Firewall     string `json:"firewall"`
		Manufacturer string `json:"manufacturer"`
		TriggerURL   string `json:"trigger_url"`
	}
	if err := decodeJSON(data, &rows); err != nil {
		return Result{}, err
	}
	if len(rows) > maxDecodedRecords {
		return Result{}, fmt.Errorf("report has more than %d records", maxDecodedRecords)
	}
	result := Result{Observations: make([]ObservationResult, 0, len(rows))}
	for _, row := range rows {
		result.Observations = append(result.Observations, observation(context, "waf.fingerprint", map[string]any{
			"url": row.URL, "detected": row.Detected, "firewall": row.Firewall, "manufacturer": row.Manufacturer,
		}))
	}
	return result, nil
}

func decodeWhatWeb(data []byte, context decodeContext) (Result, error) {
	var rows []struct {
		Target     string                     `json:"target"`
		HTTPStatus int                        `json:"http_status"`
		Plugins    map[string]json.RawMessage `json:"plugins"`
	}
	if err := decodeJSON(data, &rows); err != nil {
		return Result{}, err
	}
	if len(rows) > maxDecodedRecords {
		return Result{}, fmt.Errorf("report has more than %d records", maxDecodedRecords)
	}
	var result Result
	for _, row := range rows {
		names := make([]string, 0, len(row.Plugins))
		for name := range row.Plugins {
			names = append(names, name)
		}
		sort.Strings(names)
		result.Observations = append(result.Observations, observation(context, "web.fingerprint", map[string]any{
			"url": row.Target, "status_code": row.HTTPStatus, "plugins": names,
		}))
		if parsed, ok := absoluteHTTPURL(row.Target); ok {
			result.URLs = append(result.URLs, URLResult{URL: parsed, Visited: true})
		}
	}
	return result, nil
}

func decodeNuclei(data []byte, context decodeContext) (Result, error) {
	lines, err := scanLines(data)
	if err != nil {
		return Result{}, err
	}
	var result Result
	for index, line := range lines {
		var row struct {
			TemplateID string `json:"template-id"`
			MatchedAt  string `json:"matched-at"`
			Host       string `json:"host"`
			Info       struct {
				Name        string `json:"name"`
				Severity    string `json:"severity"`
				Description string `json:"description"`
			} `json:"info"`
		}
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return Result{}, fmt.Errorf("record %d: %w", index+1, err)
		}
		if row.TemplateID == "" || row.Info.Name == "" {
			return Result{}, fmt.Errorf("record %d is missing template-id or info.name", index+1)
		}
		severity := normalizeSeverity(row.Info.Severity)
		description := limited(row.Info.Description)
		if description == "" {
			description = "Nuclei template " + row.TemplateID + " matched"
		}
		if row.MatchedAt != "" {
			description += " at " + limited(row.MatchedAt)
		}
		result.Findings = append(result.Findings, finding(context, row.Info.Name, severity, description))
		if parsed, ok := absoluteHTTPURL(firstNonempty(row.MatchedAt, row.Host)); ok {
			result.URLs = append(result.URLs, URLResult{URL: parsed, Visited: true})
		}
	}
	return result, nil
}

func decodeWapiti(data []byte, context decodeContext) (Result, error) {
	var report struct {
		Vulnerabilities map[string][]wapitiRecord `json:"vulnerabilities"`
		Anomalies       map[string][]wapitiRecord `json:"anomalies"`
	}
	if err := decodeJSON(data, &report); err != nil {
		return Result{}, err
	}
	var result Result
	count := 0
	for _, title := range sortedKeys(report.Vulnerabilities) {
		rows := report.Vulnerabilities[title]
		for _, row := range rows {
			count++
			if count > maxDecodedRecords {
				return Result{}, fmt.Errorf("report has more than %d records", maxDecodedRecords)
			}
			result.Findings = append(result.Findings, finding(context, title, wapitiSeverity(row.Level), wapitiDescription(row)))
			if discovered, ok := resolveTargetURL(context.target.Value, row.Path); ok {
				result.URLs = append(result.URLs, URLResult{URL: discovered, Visited: true})
			}
		}
	}
	for _, title := range sortedKeys(report.Anomalies) {
		rows := report.Anomalies[title]
		for _, row := range rows {
			count++
			if count > maxDecodedRecords {
				return Result{}, fmt.Errorf("report has more than %d records", maxDecodedRecords)
			}
			result.Observations = append(result.Observations, observation(context, "scanner.anomaly", map[string]any{
				"title": title, "level": row.Level, "method": row.Method, "path": row.Path, "info": limited(row.Info),
			}))
		}
	}
	return result, nil
}

type wapitiRecord struct {
	Method    string `json:"method"`
	Path      string `json:"path"`
	Info      string `json:"info"`
	Level     int    `json:"level"`
	Parameter any    `json:"parameter"`
}

func wapitiDescription(row wapitiRecord) string {
	parts := []string{limited(row.Info)}
	if row.Method != "" || row.Path != "" {
		parts = append(parts, strings.TrimSpace(row.Method+" "+row.Path))
	}
	if row.Parameter != nil && fmt.Sprint(row.Parameter) != "" {
		parts = append(parts, "parameter "+limited(fmt.Sprint(row.Parameter)))
	}
	return joinNonempty(parts...)
}

func decodeURLList(data []byte, context decodeContext) (Result, error) {
	lines, err := scanLines(data)
	if err != nil {
		return Result{}, err
	}
	var result Result
	for _, line := range lines {
		if value, ok := absoluteHTTPURL(strings.TrimSpace(line)); ok {
			result.URLs = append(result.URLs, URLResult{URL: value})
		}
	}
	result.Observations = append(result.Observations, observation(context, "url.discovery", map[string]any{"urls": len(result.URLs)}))
	return result, nil
}

var (
	gobusterDirPattern   = regexp.MustCompile(`^(\S+)\s+\(Status:\s+\d{3}\)`)
	gobusterVHostPattern = regexp.MustCompile(`(?i)^(?:Found:\s+)?(\S+)\s+Status:\s+\d{3}\b`)
)

func decodeGobusterDir(data []byte, context decodeContext) (Result, error) {
	lines, err := scanLines(data)
	if err != nil {
		return Result{}, err
	}
	var result Result
	for _, line := range lines {
		match := gobusterDirPattern.FindStringSubmatch(line)
		if len(match) != 2 {
			continue
		}
		if value, ok := resolveTargetURL(context.target.Value, match[1]); ok {
			result.URLs = append(result.URLs, URLResult{URL: value, Visited: true})
		}
	}
	result.Observations = append(result.Observations, observation(context, "content.discovery", map[string]any{"urls": len(result.URLs)}))
	return result, nil
}

func decodeGobusterVHost(data []byte, context decodeContext) (Result, error) {
	lines, err := scanLines(data)
	if err != nil {
		return Result{}, err
	}
	base, err := url.Parse(context.target.Value)
	if err != nil {
		return Result{}, err
	}
	var result Result
	for _, line := range lines {
		match := gobusterVHostPattern.FindStringSubmatch(line)
		if len(match) != 2 {
			continue
		}
		candidate := match[1]
		if !strings.Contains(candidate, "://") {
			candidate = base.Scheme + "://" + candidate
		}
		if value, ok := absoluteHTTPURL(candidate); ok {
			result.URLs = append(result.URLs, URLResult{URL: value, Visited: true})
		}
	}
	result.Observations = append(result.Observations, observation(context, "host.discovery", map[string]any{"urls": len(result.URLs)}))
	return result, nil
}

func decodeGobusterGCS(data []byte, context decodeContext) (Result, error) {
	lines, err := scanLines(data)
	if err != nil {
		return Result{}, err
	}
	result := Result{Observations: make([]ObservationResult, 0, len(lines))}
	for _, line := range lines {
		result.Observations = append(result.Observations, observation(context, "gcs.bucket", map[string]any{"result": limited(line)}))
	}
	return result, nil
}

func decodeJSON(data []byte, destination any) error {
	decoder := json.NewDecoder(bytes.NewReader(data))
	if err := decoder.Decode(destination); err != nil {
		return err
	}
	if err := decoder.Decode(&struct{}{}); !errors.Is(err, io.EOF) {
		if err == nil {
			return fmt.Errorf("multiple JSON values")
		}
		return err
	}
	return nil
}

func scanLines(data []byte) ([]string, error) {
	scanner := bufio.NewScanner(bytes.NewReader(data))
	scanner.Buffer(make([]byte, 64<<10), maxDecodedText)
	lines := make([]string, 0)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		if len(lines) >= maxDecodedRecords {
			return nil, fmt.Errorf("report has more than %d records", maxDecodedRecords)
		}
		lines = append(lines, line)
	}
	return lines, scanner.Err()
}

func finding(context decodeContext, title, severity, description string) FindingResult {
	return FindingResult{TechniqueCode: context.technique, Title: limited(title), Severity: severity, Description: limited(description)}
}

func observation(context decodeContext, kind string, data any) ObservationResult {
	encoded, _ := json.Marshal(data)
	return ObservationResult{TechniqueCode: context.technique, Kind: kind, Data: string(encoded)}
}

func normalizeSeverity(value string) string {
	value = strings.ToLower(strings.TrimSpace(value))
	if isFindingSeverity(value) || value == model.PluginOutputRankInformational {
		return value
	}
	if value == "info" {
		return model.PluginOutputRankInformational
	}
	return model.PluginOutputRankUnranked
}

func isFindingSeverity(value string) bool {
	switch value {
	case model.PluginOutputRankLow, model.PluginOutputRankMedium, model.PluginOutputRankHigh, model.PluginOutputRankCritical:
		return true
	default:
		return false
	}
}

func wapitiSeverity(level int) string {
	switch level {
	case 4:
		return model.PluginOutputRankCritical
	case 3:
		return model.PluginOutputRankHigh
	case 2:
		return model.PluginOutputRankMedium
	case 1:
		return model.PluginOutputRankLow
	default:
		return model.PluginOutputRankInformational
	}
}

func absoluteHTTPURL(value string) (string, bool) {
	parsed, err := url.Parse(value)
	if err != nil || (parsed.Scheme != "http" && parsed.Scheme != "https") || parsed.Host == "" {
		return "", false
	}
	return parsed.String(), true
}

func resolveTargetURL(target, reference string) (string, bool) {
	base, err := url.Parse(target)
	if err != nil || base.Host == "" {
		return "", false
	}
	relative, err := url.Parse(reference)
	if err != nil {
		return "", false
	}
	return absoluteHTTPURL(base.ResolveReference(relative).String())
}

func limited(value string) string {
	value = strings.TrimSpace(value)
	if len(value) <= maxDecodedText {
		return value
	}
	return value[:maxDecodedText]
}

func joinNonempty(values ...string) string {
	result := make([]string, 0, len(values))
	for _, value := range values {
		if value = strings.TrimSpace(value); value != "" {
			result = append(result, value)
		}
	}
	return strings.Join(result, "; ")
}

func firstNonempty(values ...string) string {
	for _, value := range values {
		if value = strings.TrimSpace(value); value != "" {
			return value
		}
	}
	return ""
}

func sortedKeys[V any](values map[string]V) []string {
	keys := make([]string, 0, len(values))
	for key := range values {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}
