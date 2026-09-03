package plugin

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/fs"
	"net/url"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"sort"
	"strings"
	"time"

	"github.com/owtf/owtf/internal/model"
	"gopkg.in/yaml.v3"
)

const defaultTechniquePriority = 99

const (
	maxExternalGuidance   = 4096
	maxExternalReferences = 32
	maxExternalTitle      = 256
	maxExternalURL        = 2048
	maxGrepRules          = 64
	maxGrepPattern        = 4096
	maxGrepMatches        = 1000
	defaultGrepMatches    = 100
)

// TechniqueSpec preserves the OWTF test-group metadata referenced by a plugin.
type TechniqueSpec struct {
	Code      string `yaml:"code" json:"code"`
	Title     string `yaml:"title,omitempty" json:"title"`
	Hint      string `yaml:"hint,omitempty" json:"hint,omitempty"`
	Priority  int    `yaml:"priority,omitempty" json:"priority"`
	Reference string `yaml:"reference,omitempty" json:"reference,omitempty"`
}

// UnmarshalYAML accepts historical code-only manifests while new manifests use
// a mapping that retains the complete OWTF technique metadata.
func (t *TechniqueSpec) UnmarshalYAML(node *yaml.Node) error {
	if node.Kind == yaml.ScalarNode {
		var code string
		if err := node.Decode(&code); err != nil {
			return err
		}
		*t = TechniqueSpec{Code: code}
		return nil
	}
	if node.Kind != yaml.MappingNode {
		return fmt.Errorf("technique must be a code or mapping")
	}
	allowed := map[string]bool{"code": true, "title": true, "hint": true, "priority": true, "reference": true}
	for index := 0; index < len(node.Content); index += 2 {
		if !allowed[node.Content[index].Value] {
			return fmt.Errorf("unknown technique field %q", node.Content[index].Value)
		}
	}
	type plain TechniqueSpec
	return node.Decode((*plain)(t))
}

// UnmarshalJSON keeps stored code-only task snapshots readable.
func (t *TechniqueSpec) UnmarshalJSON(data []byte) error {
	if data = bytes.TrimSpace(data); len(data) != 0 && data[0] == '"' {
		var code string
		if err := json.Unmarshal(data, &code); err != nil {
			return err
		}
		*t = TechniqueSpec{Code: code}
		return nil
	}
	type plain TechniqueSpec
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	return decoder.Decode((*plain)(t))
}

// Manifest is the validated plugin.yaml contract retained with each task.
type Manifest struct {
	APIVersion string `yaml:"apiVersion" json:"apiVersion"`
	Kind       string `yaml:"kind" json:"kind"`
	Metadata   struct {
		ID          string `yaml:"id" json:"id"`
		Version     string `yaml:"version" json:"version"`
		Title       string `yaml:"title" json:"title"`
		Description string `yaml:"description" json:"description"`
	} `yaml:"metadata" json:"metadata"`
	Spec struct {
		Techniques   []TechniqueSpec     `yaml:"techniques" json:"techniques"`
		Group        string              `yaml:"group" json:"group"`
		Type         string              `yaml:"type" json:"type"`
		TargetKinds  []string            `yaml:"targetKinds,omitempty" json:"targetKinds,omitempty"`
		Inputs       []model.PluginInput `yaml:"inputs,omitempty" json:"inputs,omitempty"`
		Requirements struct {
			Commands []string `yaml:"commands,omitempty" json:"commands,omitempty"`
		} `yaml:"requirements,omitempty" json:"requirements,omitempty"`
		Runtime struct {
			Type      string         `yaml:"type" json:"type"`
			Builtin   string         `yaml:"builtin,omitempty" json:"builtin,omitempty"`
			Command   *CommandSpec   `yaml:"command,omitempty" json:"command,omitempty"`
			Container *ContainerSpec `yaml:"container,omitempty" json:"container,omitempty"`
			External  *ExternalSpec  `yaml:"external,omitempty" json:"external,omitempty"`
			Grep      *GrepSpec      `yaml:"grep,omitempty" json:"grep,omitempty"`
		} `yaml:"runtime" json:"runtime"`
	} `yaml:"spec" json:"spec"`
}

// CommandSpec defines direct executable invocation without a shell.
type CommandSpec struct {
	Executable string            `yaml:"executable" json:"executable"`
	Args       []string          `yaml:"args,omitempty" json:"args,omitempty"`
	Artifacts  []CommandArtifact `yaml:"artifacts,omitempty" json:"artifacts,omitempty"`
}

// ContainerSpec defines a shell-free command executed in a pre-existing image.
// Images are never pulled implicitly by OWTF.
type ContainerSpec struct {
	Image      string            `yaml:"image" json:"image"`
	Executable string            `yaml:"executable" json:"executable"`
	Args       []string          `yaml:"args,omitempty" json:"args,omitempty"`
	Artifacts  []CommandArtifact `yaml:"artifacts,omitempty" json:"artifacts,omitempty"`
}

// ExternalSpec contains static resources for an OWTF external plugin. It has
// no executable component and never sends traffic to the target.
type ExternalSpec struct {
	Guidance   string                    `yaml:"guidance" json:"guidance"`
	References []model.ExternalReference `yaml:"references" json:"references"`
}

// GrepSpec contains bounded RE2 rules evaluated over retained transactions.
type GrepSpec struct {
	MaxMatches int        `yaml:"maxMatches,omitempty" json:"maxMatches"`
	Rules      []GrepRule `yaml:"rules" json:"rules"`
}

// GrepRule searches one explicit part of each captured transaction.
type GrepRule struct {
	ID      string `yaml:"id" json:"id"`
	Title   string `yaml:"title" json:"title"`
	Source  string `yaml:"source" json:"source"`
	Pattern string `yaml:"pattern" json:"pattern"`
}

// CommandArtifact declares a file a command plugin may emit in its assigned
// artifact directory.
type CommandArtifact struct {
	Name      string `yaml:"name" json:"name"`
	MediaType string `yaml:"mediaType,omitempty" json:"mediaType,omitempty"`
	Required  bool   `yaml:"required,omitempty" json:"required,omitempty"`
}

// ArtifactResult is immutable evidence returned by a plugin execution.
type ArtifactResult struct {
	Name      string
	MediaType string
	Data      []byte
}

// TransactionResult is HTTP transaction metadata returned by a plugin.
type TransactionResult struct {
	Method                   string
	URL                      string
	RequestHeaders           string
	StatusCode               int
	ResponseHeaders          string
	ResponseBodyArtifactName string
	DurationMS               int64
}

// ObservationResult is a factual plugin output that is not yet a finding.
type ObservationResult struct {
	TechniqueCode string
	Kind          string
	Data          string
}

// FindingResult is a plugin-proposed security conclusion.
type FindingResult struct {
	TechniqueCode string
	Title         string
	Severity      string
	Description   string
}

// Result contains all structured output produced by one plugin execution.
type Result struct {
	Artifacts    []ArtifactResult
	Transactions []TransactionResult
	Observations []ObservationResult
	Findings     []FindingResult
}

// Request provides the target and event logger available to an executor.
type Request struct {
	TaskID       string
	PluginID     string
	Target       model.Target
	Inputs       map[string]any
	Transactions TransactionReader
	Log          func(stream, message string)
}

// Executor runs one plugin against one target.
type Executor func(context.Context, Request) (Result, error)

// Entry combines a manifest with resolved availability and executable behavior.
type Entry struct {
	Manifest     Manifest
	Availability string
	Reason       string
	Executor     Executor
}

// Catalog is the validated plugin set available to the current server process.
type Catalog struct {
	entries map[string]Entry
}

// Load recursively discovers plugin.yaml files and rejects an invalid catalog as
// a unit so startup cannot silently omit malformed plugins.
func Load(fsys fs.FS) (*Catalog, error) {
	catalog := &Catalog{entries: make(map[string]Entry)}
	techniques := make(map[string]TechniqueSpec)
	err := fs.WalkDir(fsys, ".", func(path string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if d.IsDir() || d.Name() != "plugin.yaml" {
			return nil
		}
		data, err := fs.ReadFile(fsys, path)
		if err != nil {
			return err
		}
		var manifest Manifest
		decoder := yaml.NewDecoder(strings.NewReader(string(data)))
		decoder.KnownFields(true)
		if err := decoder.Decode(&manifest); err != nil {
			return fmt.Errorf("parse %s: %w", path, err)
		}
		normalizeManifest(&manifest)
		if err := validateManifest(manifest); err != nil {
			return fmt.Errorf("validate %s: %w", path, err)
		}
		if _, exists := catalog.entries[manifest.Metadata.ID]; exists {
			return fmt.Errorf("duplicate plugin ID %q", manifest.Metadata.ID)
		}
		technique := manifest.Spec.Techniques[0]
		if existing, ok := techniques[technique.Code]; ok && existing != technique {
			return fmt.Errorf("plugin %q conflicts with metadata for technique %q", manifest.Metadata.ID, technique.Code)
		}
		techniques[technique.Code] = technique
		entry := Entry{
			Manifest: manifest, Availability: "missing_runtime", Reason: "runtime is not registered",
		}
		switch manifest.Spec.Runtime.Type {
		case "external":
			entry.Availability = "ready"
			entry.Reason = ""
			entry.Executor = ExternalExecutor(manifest)
		case "grep":
			entry.Availability = "ready"
			entry.Reason = ""
			entry.Executor = GrepExecutor(manifest)
		}
		catalog.entries[manifest.Metadata.ID] = entry
		return nil
	})
	if err != nil {
		return nil, err
	}
	return catalog, nil
}

func normalizeManifest(manifest *Manifest) {
	for index := range manifest.Spec.Techniques {
		technique := &manifest.Spec.Techniques[index]
		technique.Code = strings.TrimSpace(technique.Code)
		technique.Title = strings.TrimSpace(technique.Title)
		technique.Hint = strings.TrimSpace(technique.Hint)
		technique.Reference = strings.TrimSpace(technique.Reference)
		if technique.Title == "" {
			technique.Title = strings.TrimSpace(manifest.Metadata.Title)
		}
		if technique.Priority == 0 {
			technique.Priority = defaultTechniquePriority
		}
	}
	if external := manifest.Spec.Runtime.External; external != nil {
		external.Guidance = strings.TrimSpace(external.Guidance)
		for index := range external.References {
			external.References[index].Title = strings.TrimSpace(external.References[index].Title)
			external.References[index].URL = strings.TrimSpace(external.References[index].URL)
		}
	}
	if grep := manifest.Spec.Runtime.Grep; grep != nil {
		if grep.MaxMatches == 0 {
			grep.MaxMatches = defaultGrepMatches
		}
		for index := range grep.Rules {
			grep.Rules[index].ID = strings.TrimSpace(grep.Rules[index].ID)
			grep.Rules[index].Title = strings.TrimSpace(grep.Rules[index].Title)
			grep.Rules[index].Source = strings.TrimSpace(grep.Rules[index].Source)
			grep.Rules[index].Pattern = strings.TrimSpace(grep.Rules[index].Pattern)
		}
	}
}

func validateManifest(manifest Manifest) error {
	if manifest.APIVersion != "owtf.dev/v1alpha1" {
		return fmt.Errorf("unsupported apiVersion %q", manifest.APIVersion)
	}
	if manifest.Kind != "Plugin" {
		return fmt.Errorf("kind must be Plugin")
	}
	if manifest.Metadata.ID == "" || manifest.Metadata.Version == "" || manifest.Metadata.Title == "" {
		return fmt.Errorf("metadata.id, metadata.version, and metadata.title are required")
	}
	if len(manifest.Spec.Techniques) != 1 {
		return fmt.Errorf("exactly one technique is required")
	}
	if !validPluginGroup(manifest.Spec.Group) {
		return fmt.Errorf("unsupported plugin group %q", manifest.Spec.Group)
	}
	if !validPluginType(manifest.Spec.Type) {
		return fmt.Errorf("unsupported plugin type %q", manifest.Spec.Type)
	}
	technique := manifest.Spec.Techniques[0]
	if technique.Code == "" || technique.Title == "" || technique.Priority < 1 {
		return fmt.Errorf("technique code, title, and positive priority are required")
	}
	if manifest.Metadata.ID != technique.Code+"-"+manifest.Spec.Type {
		return fmt.Errorf("plugin ID must be %q", technique.Code+"-"+manifest.Spec.Type)
	}
	if technique.Reference != "" {
		reference, err := url.Parse(technique.Reference)
		if err != nil || (reference.Scheme != "http" && reference.Scheme != "https") || reference.Host == "" {
			return fmt.Errorf("technique %q has invalid reference %q", technique.Code, technique.Reference)
		}
	}
	inputNames, err := validateInputs(manifest.Spec.Inputs)
	if err != nil {
		return err
	}
	switch manifest.Spec.Runtime.Type {
	case "builtin":
		if manifest.Spec.Runtime.Builtin == "" || manifest.Spec.Runtime.Command != nil || manifest.Spec.Runtime.Container != nil || manifest.Spec.Runtime.External != nil || manifest.Spec.Runtime.Grep != nil {
			return fmt.Errorf("builtin runtime requires only a builtin name")
		}
	case "command":
		if manifest.Spec.Runtime.Builtin != "" || manifest.Spec.Runtime.Container != nil || manifest.Spec.Runtime.External != nil || manifest.Spec.Runtime.Grep != nil {
			return fmt.Errorf("command runtime requires only a command")
		}
		if err := validateCommand(manifest.Spec.Runtime.Command, inputNames); err != nil {
			return err
		}
	case "container":
		if manifest.Spec.Runtime.Builtin != "" || manifest.Spec.Runtime.Command != nil || manifest.Spec.Runtime.External != nil || manifest.Spec.Runtime.Grep != nil {
			return fmt.Errorf("container runtime requires only a container")
		}
		if err := validateContainer(manifest.Spec.Runtime.Container, inputNames); err != nil {
			return err
		}
	case "external":
		if manifest.Spec.Runtime.Builtin != "" || manifest.Spec.Runtime.Command != nil || manifest.Spec.Runtime.Container != nil || manifest.Spec.Runtime.Grep != nil {
			return fmt.Errorf("external runtime requires only external guidance")
		}
		if len(manifest.Spec.Requirements.Commands) != 0 {
			return fmt.Errorf("external runtime cannot require commands")
		}
		if err := validateExternal(manifest.Spec.Runtime.External); err != nil {
			return err
		}
	case "grep":
		if manifest.Spec.Runtime.Builtin != "" || manifest.Spec.Runtime.Command != nil || manifest.Spec.Runtime.Container != nil || manifest.Spec.Runtime.External != nil {
			return fmt.Errorf("grep runtime requires only grep rules")
		}
		if len(manifest.Spec.Requirements.Commands) != 0 {
			return fmt.Errorf("grep runtime cannot require commands")
		}
		if err := validateGrep(manifest.Spec.Runtime.Grep); err != nil {
			return err
		}
	default:
		return fmt.Errorf("runtime type %q is not implemented", manifest.Spec.Runtime.Type)
	}
	return nil
}

func validPluginGroup(group string) bool {
	switch group {
	case "web", "network", "auxiliary":
		return true
	default:
		return false
	}
}

func validPluginType(pluginType string) bool {
	switch pluginType {
	case "passive", "semi_passive", "active", "grep", "external", "bruteforce", "dos", "exploit", "selenium", "smb":
		return true
	default:
		return false
	}
}

func validateCommand(command *CommandSpec, inputs map[string]bool) error {
	if command == nil || strings.TrimSpace(command.Executable) == "" {
		return fmt.Errorf("command runtime requires an executable")
	}
	if strings.Contains(command.Executable, "{{") {
		return fmt.Errorf("command executable cannot contain placeholders")
	}
	switch filepath.Base(command.Executable) {
	case "sh", "bash", "dash", "zsh", "ksh", "fish", "pwsh", "powershell":
		return fmt.Errorf("shell interpreters require the future strict-shell runtime")
	}
	artifacts := make(map[string]bool, len(command.Artifacts))
	for _, artifact := range command.Artifacts {
		if !validArtifactName(artifact.Name) || artifacts[artifact.Name] {
			return fmt.Errorf("invalid or duplicate command artifact name %q", artifact.Name)
		}
		artifacts[artifact.Name] = true
	}
	for _, arg := range command.Args {
		if !strings.Contains(arg, "{{") {
			continue
		}
		if arg == "{{target}}" {
			continue
		}
		if strings.HasPrefix(arg, "{{artifact:") && strings.HasSuffix(arg, "}}") && artifacts[strings.TrimSuffix(strings.TrimPrefix(arg, "{{artifact:"), "}}")] {
			continue
		}
		if strings.HasPrefix(arg, "{{input:") && strings.HasSuffix(arg, "}}") && inputs[strings.TrimSuffix(strings.TrimPrefix(arg, "{{input:"), "}}")] {
			continue
		}
		return fmt.Errorf("argument %q contains an unsupported or partial placeholder", arg)
	}
	return nil
}

func validateContainer(container *ContainerSpec, inputs map[string]bool) error {
	if container == nil {
		return fmt.Errorf("container runtime requires a container")
	}
	if strings.TrimSpace(container.Image) == "" || strings.ContainsAny(container.Image, " \t\r\n") {
		return fmt.Errorf("container runtime requires one image reference without whitespace")
	}
	command := &CommandSpec{
		Executable: container.Executable,
		Args:       container.Args,
		Artifacts:  container.Artifacts,
	}
	if err := validateCommand(command, inputs); err != nil {
		return fmt.Errorf("container %w", err)
	}
	return nil
}

func validateExternal(external *ExternalSpec) error {
	if external == nil || external.Guidance == "" {
		return fmt.Errorf("external runtime requires guidance")
	}
	if len(external.Guidance) > maxExternalGuidance {
		return fmt.Errorf("external guidance exceeds %d bytes", maxExternalGuidance)
	}
	if len(external.References) == 0 || len(external.References) > maxExternalReferences {
		return fmt.Errorf("external runtime requires 1 to %d references", maxExternalReferences)
	}
	seen := make(map[string]bool, len(external.References))
	for _, reference := range external.References {
		if reference.Title == "" || len(reference.Title) > maxExternalTitle {
			return fmt.Errorf("external reference title must contain 1 to %d bytes", maxExternalTitle)
		}
		if len(reference.URL) == 0 || len(reference.URL) > maxExternalURL || seen[reference.URL] {
			return fmt.Errorf("external reference %q has an invalid or duplicate URL", reference.Title)
		}
		parsed, err := url.Parse(reference.URL)
		if err != nil || (parsed.Scheme != "http" && parsed.Scheme != "https") || parsed.Host == "" || parsed.User != nil {
			return fmt.Errorf("external reference %q has invalid URL %q", reference.Title, reference.URL)
		}
		seen[reference.URL] = true
	}
	return nil
}

func validateGrep(grep *GrepSpec) error {
	if grep == nil || len(grep.Rules) == 0 || len(grep.Rules) > maxGrepRules {
		return fmt.Errorf("grep runtime requires 1 to %d rules", maxGrepRules)
	}
	if grep.MaxMatches < 1 || grep.MaxMatches > maxGrepMatches {
		return fmt.Errorf("grep maxMatches must be between 1 and %d", maxGrepMatches)
	}
	seen := make(map[string]bool, len(grep.Rules))
	for _, rule := range grep.Rules {
		if !validGrepRuleID(rule.ID) || seen[rule.ID] {
			return fmt.Errorf("invalid or duplicate grep rule ID %q", rule.ID)
		}
		seen[rule.ID] = true
		if rule.Title == "" || len(rule.Title) > maxExternalTitle {
			return fmt.Errorf("grep rule %q title must contain 1 to %d bytes", rule.ID, maxExternalTitle)
		}
		if !validGrepSource(rule.Source) {
			return fmt.Errorf("grep rule %q has unsupported source %q", rule.ID, rule.Source)
		}
		if rule.Pattern == "" || len(rule.Pattern) > maxGrepPattern {
			return fmt.Errorf("grep rule %q pattern must contain 1 to %d bytes", rule.ID, maxGrepPattern)
		}
		if _, err := regexp.Compile(rule.Pattern); err != nil {
			return fmt.Errorf("grep rule %q pattern: %w", rule.ID, err)
		}
	}
	return nil
}

func validGrepRuleID(value string) bool {
	if len(value) == 0 || len(value) > 64 || value[0] < 'a' || value[0] > 'z' {
		return false
	}
	for _, character := range value[1:] {
		if character >= 'a' && character <= 'z' || character >= '0' && character <= '9' || character == '-' || character == '_' {
			continue
		}
		return false
	}
	return true
}

func validGrepSource(source string) bool {
	switch source {
	case "url", "request_headers", "response_headers", "request_body", "response_body":
		return true
	default:
		return false
	}
}

func validArtifactName(name string) bool {
	if name == "" || len(name) > 128 || name == "." || name == ".." {
		return false
	}
	for _, char := range name {
		if (char < 'a' || char > 'z') && (char < 'A' || char > 'Z') && (char < '0' || char > '9') && char != '.' && char != '_' && char != '-' {
			return false
		}
	}
	return true
}

// RegisterBuiltin attaches an in-process executor to manifests naming it.
func (c *Catalog) RegisterBuiltin(name string, executor Executor) {
	for id, entry := range c.entries {
		if entry.Manifest.Spec.Runtime.Type == "builtin" && entry.Manifest.Spec.Runtime.Builtin == name {
			entry.Executor = executor
			entry.Availability = "ready"
			entry.Reason = ""
			c.entries[id] = entry
		}
	}
}

// ResolveCommands checks command requirements and marks each command plugin as
// ready, unsupported, or missing requirements.
func (c *Catalog) ResolveCommands() {
	for id, entry := range c.entries {
		if entry.Manifest.Spec.Runtime.Type != "command" {
			continue
		}
		if runtime.GOOS == "windows" {
			entry.Availability = "unsupported"
			entry.Reason = "command plugins currently require Linux or macOS process groups"
			c.entries[id] = entry
			continue
		}
		command := entry.Manifest.Spec.Runtime.Command
		resolved, err := exec.LookPath(command.Executable)
		missing := make([]string, 0)
		if err != nil {
			missing = append(missing, command.Executable)
		}
		for _, required := range entry.Manifest.Spec.Requirements.Commands {
			if _, err := exec.LookPath(required); err != nil {
				missing = append(missing, required)
			}
		}
		if len(missing) > 0 {
			entry.Availability = "missing_requirements"
			entry.Reason = "missing commands: " + strings.Join(unique(missing), ", ")
		} else {
			entry.Executor = CommandExecutor(entry.Manifest, resolved)
			entry.Availability = "ready"
			entry.Reason = ""
		}
		c.entries[id] = entry
	}
}

// ResolveContainers checks local image availability without pulling or running
// an image. Container plugins stay visible with an exact unavailable reason.
func (c *Catalog) ResolveContainers(ctx context.Context, engine ContainerEngine) {
	for id, entry := range c.entries {
		if entry.Manifest.Spec.Runtime.Type != "container" {
			continue
		}
		if engine == nil {
			entry.Availability = "missing_runtime"
			entry.Reason = "container engine is not configured"
			c.entries[id] = entry
			continue
		}
		checkCtx, cancel := context.WithTimeout(ctx, 3*time.Second)
		err := engine.ImageAvailable(checkCtx, entry.Manifest.Spec.Runtime.Container.Image)
		cancel()
		if err != nil {
			entry.Availability = "missing_requirements"
			entry.Reason = err.Error()
			c.entries[id] = entry
			continue
		}
		entry.Executor = ContainerExecutor(entry.Manifest, engine)
		entry.Availability = "ready"
		entry.Reason = ""
		c.entries[id] = entry
	}
}

func unique(values []string) []string {
	seen := make(map[string]bool, len(values))
	result := make([]string, 0, len(values))
	for _, value := range values {
		if !seen[value] {
			seen[value] = true
			result = append(result, value)
		}
	}
	return result
}

// Get returns the catalog entry for a stable plugin ID.
func (c *Catalog) Get(id string) (Entry, bool) {
	entry, ok := c.entries[id]
	return entry, ok
}

// Entries returns a stable, plugin-ID-sorted snapshot of the catalog.
func (c *Catalog) Entries() []Entry {
	entries := make([]Entry, 0, len(c.entries))
	for _, entry := range c.entries {
		entries = append(entries, entry)
	}
	sort.Slice(entries, func(i, j int) bool {
		return entries[i].Manifest.Metadata.ID < entries[j].Manifest.Metadata.ID
	})
	return entries
}

// EntriesByGroupType returns plugins in an OWTF plugin group, optionally
// limited to the supplied plugin types.
func (c *Catalog) EntriesByGroupType(group string, pluginTypes []string) []Entry {
	wantedTypes := make(map[string]bool, len(pluginTypes))
	for _, pluginType := range pluginTypes {
		wantedTypes[pluginType] = true
	}
	entries := make([]Entry, 0)
	for _, entry := range c.Entries() {
		if entry.Manifest.Spec.Group != group {
			continue
		}
		if len(wantedTypes) != 0 && !wantedTypes[entry.Manifest.Spec.Type] {
			continue
		}
		entries = append(entries, entry)
	}
	return entries
}

// Plugin returns the operator-visible catalog record for an entry.
func (e Entry) Plugin() model.Plugin {
	techniques := make([]model.Technique, len(e.Manifest.Spec.Techniques))
	for index, technique := range e.Manifest.Spec.Techniques {
		techniques[index] = model.Technique{
			Code: technique.Code, Title: technique.Title, Hint: technique.Hint,
			Priority: technique.Priority, Reference: technique.Reference,
		}
	}
	return model.Plugin{
		ID:           e.Manifest.Metadata.ID,
		Version:      e.Manifest.Metadata.Version,
		Title:        e.Manifest.Metadata.Title,
		Description:  e.Manifest.Metadata.Description,
		Group:        e.Manifest.Spec.Group,
		Type:         e.Manifest.Spec.Type,
		Techniques:   techniques,
		Inputs:       append([]model.PluginInput{}, e.Manifest.Spec.Inputs...),
		RuntimeType:  e.Manifest.Spec.Runtime.Type,
		Availability: e.Availability,
		Reason:       e.Reason,
	}
}

// SupportsTarget reports whether an entry accepts the normalized target kind.
func (e Entry) SupportsTarget(kind string) bool {
	return supportsTarget(e.Manifest.Spec.TargetKinds, kind)
}
