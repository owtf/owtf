package plugin

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"sort"
	"strconv"
	"strings"

	"github.com/owtf/owtf/internal/model"
)

const (
	maxPluginInputs = 64
	maxInputName    = 64
	maxInputString  = 16 << 10
)

// TaskSnapshot is the immutable plugin definition and resolved input set saved
// when a task is created.
type TaskSnapshot struct {
	Version  int            `json:"version"`
	Manifest Manifest       `json:"manifest"`
	Inputs   map[string]any `json:"inputs"`
}

func validateInputs(inputs []model.PluginInput) (map[string]bool, error) {
	if len(inputs) > maxPluginInputs {
		return nil, fmt.Errorf("plugin declares more than %d inputs", maxPluginInputs)
	}
	names := make(map[string]bool, len(inputs))
	for _, input := range inputs {
		if !validInputName(input.Name) || names[input.Name] {
			return nil, fmt.Errorf("invalid or duplicate input name %q", input.Name)
		}
		if len(input.Description) > 512 {
			return nil, fmt.Errorf("input %q description exceeds 512 characters", input.Name)
		}
		switch input.Type {
		case "string":
		case "integer", "boolean":
			if len(input.Choices) != 0 {
				return nil, fmt.Errorf("input %q choices require string type", input.Name)
			}
		default:
			return nil, fmt.Errorf("input %q has unsupported type %q", input.Name, input.Type)
		}
		if input.Type != "integer" && (input.Minimum != nil || input.Maximum != nil) {
			return nil, fmt.Errorf("input %q bounds require integer type", input.Name)
		}
		if input.Minimum != nil && input.Maximum != nil && *input.Minimum > *input.Maximum {
			return nil, fmt.Errorf("input %q minimum exceeds maximum", input.Name)
		}
		seenChoices := make(map[string]bool, len(input.Choices))
		for _, choice := range input.Choices {
			if choice == "" || len(choice) > maxInputString || seenChoices[choice] {
				return nil, fmt.Errorf("input %q has an invalid or duplicate choice", input.Name)
			}
			seenChoices[choice] = true
		}
		if input.Default != nil {
			if _, err := normalizeInput(input, input.Default); err != nil {
				return nil, fmt.Errorf("input %q default: %w", input.Name, err)
			}
		}
		names[input.Name] = true
	}
	return names, nil
}

func validInputName(name string) bool {
	if len(name) == 0 || len(name) > maxInputName || name[0] < 'a' || name[0] > 'z' {
		return false
	}
	for _, char := range name[1:] {
		if (char < 'a' || char > 'z') && (char < '0' || char > '9') && char != '_' {
			return false
		}
	}
	return true
}

// ResolveInputs validates provided values and applies manifest defaults.
func (e Entry) ResolveInputs(provided map[string]any) (map[string]any, error) {
	specs := make(map[string]model.PluginInput, len(e.Manifest.Spec.Inputs))
	for _, input := range e.Manifest.Spec.Inputs {
		specs[input.Name] = input
	}
	unknown := make([]string, 0)
	for name := range provided {
		if _, ok := specs[name]; !ok {
			unknown = append(unknown, name)
		}
	}
	if len(unknown) != 0 {
		sort.Strings(unknown)
		return nil, fmt.Errorf("unknown inputs: %s", strings.Join(unknown, ", "))
	}
	resolved := make(map[string]any, len(e.Manifest.Spec.Inputs))
	for _, input := range e.Manifest.Spec.Inputs {
		value, ok := provided[input.Name]
		if !ok {
			value, ok = input.Default, input.Default != nil
		}
		if !ok {
			if input.Required {
				return nil, fmt.Errorf("input %q is required", input.Name)
			}
			continue
		}
		normalized, err := normalizeInput(input, value)
		if err != nil {
			return nil, fmt.Errorf("input %q: %w", input.Name, err)
		}
		resolved[input.Name] = normalized
	}
	return resolved, nil
}

func normalizeInput(input model.PluginInput, value any) (any, error) {
	switch input.Type {
	case "string":
		text, ok := value.(string)
		if !ok {
			return nil, errors.New("must be a string")
		}
		if len(text) > maxInputString {
			return nil, fmt.Errorf("exceeds %d bytes", maxInputString)
		}
		if len(input.Choices) != 0 {
			for _, choice := range input.Choices {
				if text == choice {
					return text, nil
				}
			}
			return nil, fmt.Errorf("must be one of %s", strings.Join(input.Choices, ", "))
		}
		return text, nil
	case "boolean":
		switch typed := value.(type) {
		case bool:
			return typed, nil
		case string:
			if typed == "true" {
				return true, nil
			}
			if typed == "false" {
				return false, nil
			}
		}
		return nil, errors.New("must be true or false")
	case "integer":
		integer, ok := integerValue(value)
		if !ok {
			return nil, errors.New("must be an integer")
		}
		if input.Minimum != nil && integer < *input.Minimum {
			return nil, fmt.Errorf("must be at least %d", *input.Minimum)
		}
		if input.Maximum != nil && integer > *input.Maximum {
			return nil, fmt.Errorf("must be at most %d", *input.Maximum)
		}
		return integer, nil
	default:
		return nil, fmt.Errorf("has unsupported type %q", input.Type)
	}
}

func integerValue(value any) (int64, bool) {
	switch typed := value.(type) {
	case int:
		return int64(typed), true
	case int64:
		return typed, true
	case float64:
		if math.IsInf(typed, 0) || math.IsNaN(typed) || math.Trunc(typed) != typed {
			return 0, false
		}
		integer, err := strconv.ParseInt(strconv.FormatFloat(typed, 'f', -1, 64), 10, 64)
		return integer, err == nil
	case json.Number:
		integer, err := typed.Int64()
		return integer, err == nil
	case string:
		integer, err := strconv.ParseInt(typed, 10, 64)
		return integer, err == nil
	}
	return 0, false
}

func inputArgument(value any) (string, error) {
	switch typed := value.(type) {
	case string:
		return typed, nil
	case bool:
		return strconv.FormatBool(typed), nil
	case int64:
		return strconv.FormatInt(typed, 10), nil
	default:
		return "", fmt.Errorf("unsupported resolved input type %T", value)
	}
}

// Snapshot resolves provided values and serializes the complete task contract.
func (e Entry) Snapshot(provided map[string]any) (string, error) {
	inputs, err := e.ResolveInputs(provided)
	if err != nil {
		return "", err
	}
	data, err := json.Marshal(TaskSnapshot{Version: 1, Manifest: e.Manifest, Inputs: inputs})
	return string(data), err
}

// ParseSnapshot validates a stored task snapshot. Raw manifests from databases
// created before task inputs are accepted as version-zero snapshots.
func ParseSnapshot(data string) (TaskSnapshot, error) {
	var probe struct {
		Version    int    `json:"version"`
		APIVersion string `json:"apiVersion"`
	}
	if err := json.Unmarshal([]byte(data), &probe); err != nil {
		return TaskSnapshot{}, fmt.Errorf("decode plugin snapshot: %w", err)
	}
	if probe.Version == 0 && probe.APIVersion != "" {
		var manifest Manifest
		if err := decodeSnapshot(data, &manifest); err != nil {
			return TaskSnapshot{}, fmt.Errorf("decode legacy plugin snapshot: %w", err)
		}
		normalizeManifest(&manifest)
		if err := validateManifest(manifest); err != nil {
			return TaskSnapshot{}, fmt.Errorf("validate legacy plugin snapshot: %w", err)
		}
		return TaskSnapshot{Manifest: manifest, Inputs: map[string]any{}}, nil
	}
	if probe.Version != 1 {
		return TaskSnapshot{}, fmt.Errorf("unsupported plugin snapshot version %d", probe.Version)
	}
	var snapshot TaskSnapshot
	if err := decodeSnapshot(data, &snapshot); err != nil {
		return TaskSnapshot{}, fmt.Errorf("decode plugin snapshot: %w", err)
	}
	normalizeManifest(&snapshot.Manifest)
	if err := validateManifest(snapshot.Manifest); err != nil {
		return TaskSnapshot{}, fmt.Errorf("validate plugin snapshot: %w", err)
	}
	entry := Entry{Manifest: snapshot.Manifest}
	inputs, err := entry.ResolveInputs(snapshot.Inputs)
	if err != nil {
		return TaskSnapshot{}, fmt.Errorf("validate plugin snapshot inputs: %w", err)
	}
	snapshot.Inputs = inputs
	return snapshot, nil
}

func decodeSnapshot(data string, destination any) error {
	decoder := json.NewDecoder(strings.NewReader(data))
	decoder.DisallowUnknownFields()
	decoder.UseNumber()
	if err := decoder.Decode(destination); err != nil {
		return err
	}
	if err := decoder.Decode(&struct{}{}); !errors.Is(err, io.EOF) {
		if err == nil {
			return errors.New("multiple JSON values")
		}
		return err
	}
	return nil
}

// Matches reports whether the catalog still contains the exact manifest saved
// with the task. A changed plugin must be launched as new work.
func (snapshot TaskSnapshot) Matches(manifest Manifest) bool {
	want, wantErr := json.Marshal(snapshot.Manifest)
	got, gotErr := json.Marshal(manifest)
	return wantErr == nil && gotErr == nil && bytes.Equal(want, got)
}
