package plugin

import (
	"context"
	"encoding/json"
	"fmt"
	"io/fs"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"

	"github.com/owtf/owtf/internal/model"
	"gopkg.in/yaml.v3"
)

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
		Techniques   []string `yaml:"techniques" json:"techniques"`
		Group        string   `yaml:"group" json:"group"`
		Type         string   `yaml:"type" json:"type"`
		TargetKinds  []string `yaml:"targetKinds,omitempty" json:"targetKinds,omitempty"`
		Requirements struct {
			Commands []string `yaml:"commands,omitempty" json:"commands,omitempty"`
		} `yaml:"requirements,omitempty" json:"requirements,omitempty"`
		Runtime struct {
			Type    string       `yaml:"type" json:"type"`
			Builtin string       `yaml:"builtin,omitempty" json:"builtin,omitempty"`
			Command *CommandSpec `yaml:"command,omitempty" json:"command,omitempty"`
		} `yaml:"runtime" json:"runtime"`
	} `yaml:"spec" json:"spec"`
}

// CommandSpec defines direct executable invocation without a shell.
type CommandSpec struct {
	Executable string            `yaml:"executable" json:"executable"`
	Args       []string          `yaml:"args,omitempty" json:"args,omitempty"`
	Artifacts  []CommandArtifact `yaml:"artifacts,omitempty" json:"artifacts,omitempty"`
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

// ExchangeResult is HTTP transaction metadata returned by a plugin.
type ExchangeResult struct {
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
	Exchanges    []ExchangeResult
	Observations []ObservationResult
	Findings     []FindingResult
}

// Request provides the target and event logger available to an executor.
type Request struct {
	Target model.Target
	Log    func(stream, message string)
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
		if err := validateManifest(manifest); err != nil {
			return fmt.Errorf("validate %s: %w", path, err)
		}
		if _, exists := catalog.entries[manifest.Metadata.ID]; exists {
			return fmt.Errorf("duplicate plugin ID %q", manifest.Metadata.ID)
		}
		catalog.entries[manifest.Metadata.ID] = Entry{
			Manifest: manifest, Availability: "missing_runtime", Reason: "runtime is not registered",
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	return catalog, nil
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
	if len(manifest.Spec.Techniques) == 0 {
		return fmt.Errorf("at least one technique is required")
	}
	if !validPluginGroup(manifest.Spec.Group) {
		return fmt.Errorf("unsupported plugin group %q", manifest.Spec.Group)
	}
	if !validPluginType(manifest.Spec.Type) {
		return fmt.Errorf("unsupported plugin type %q", manifest.Spec.Type)
	}
	switch manifest.Spec.Runtime.Type {
	case "builtin":
		if manifest.Spec.Runtime.Builtin == "" || manifest.Spec.Runtime.Command != nil {
			return fmt.Errorf("builtin runtime requires only a builtin name")
		}
	case "command":
		if err := validateCommand(manifest.Spec.Runtime.Command); err != nil {
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

func validateCommand(command *CommandSpec) error {
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
		return fmt.Errorf("argument %q contains an unsupported or partial placeholder", arg)
	}
	return nil
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
	return model.Plugin{
		ID:           e.Manifest.Metadata.ID,
		Version:      e.Manifest.Metadata.Version,
		Title:        e.Manifest.Metadata.Title,
		Description:  e.Manifest.Metadata.Description,
		Group:        e.Manifest.Spec.Group,
		Type:         e.Manifest.Spec.Type,
		Techniques:   append([]string(nil), e.Manifest.Spec.Techniques...),
		RuntimeType:  e.Manifest.Spec.Runtime.Type,
		Availability: e.Availability,
		Reason:       e.Reason,
	}
}

// SupportsTarget reports whether an entry accepts the normalized target kind.
func (e Entry) SupportsTarget(kind string) bool {
	return supportsTarget(e.Manifest.Spec.TargetKinds, kind)
}

// Snapshot serializes the exact manifest retained with a queued task.
func (e Entry) Snapshot() (string, error) {
	data, err := json.Marshal(e.Manifest)
	return string(data), err
}
