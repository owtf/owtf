package plugin

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"unicode/utf8"

	"github.com/owtf/owtf/internal/model"
)

const (
	maxCommandOutput = 256 << 10
	maxArtifactSize  = 10 << 20
	maxLogEvents     = 1000
	maxWordlistLine  = 4 << 10
)

// CommandExecutor returns an executor that invokes executable with a validated
// argument array and an isolated temporary artifact directory.
func CommandExecutor(manifest Manifest, executable, wordlistDirectory string) Executor {
	return func(ctx context.Context, request Request) (Result, error) {
		if !supportsTarget(manifest.Spec.TargetKinds, request.Target.Kind) {
			return Result{}, fmt.Errorf("plugin does not support %s targets", request.Target.Kind)
		}
		workDir, err := os.MkdirTemp("", "owtf-plugin-*")
		if err != nil {
			return Result{}, fmt.Errorf("create plugin directory: %w", err)
		}
		defer os.RemoveAll(workDir)

		inputs, err := materializeWordlists(manifest.Spec.Inputs, request.Inputs, wordlistDirectory, workDir)
		if err != nil {
			return Result{}, err
		}
		args, err := commandArgs(manifest.Spec.Runtime.Command, request.Target.Value, workDir, inputs)
		if err != nil {
			return Result{}, err
		}
		request.Log("system", "exec "+formatCommand(executable, args))
		command := exec.Command(executable, args...)
		command.Dir = workDir
		command.Env = commandEnvironment(request, workDir)
		stdout := &eventWriter{stream: "stdout", log: request.Log, remaining: maxCommandOutput}
		stderr := &eventWriter{stream: "stderr", log: request.Log, remaining: maxCommandOutput}
		command.Stdout = stdout
		command.Stderr = stderr
		err = executeProcess(ctx, command)
		stdout.Close()
		stderr.Close()
		if err != nil {
			return Result{}, fmt.Errorf("command failed: %w", err)
		}

		artifacts, err := readCommandArtifacts(workDir, manifest.Spec.Runtime.Command.Artifacts)
		if err != nil {
			return Result{}, err
		}
		result, err := decodeArtifacts(manifest, request.Target, artifacts)
		if err != nil {
			return Result{}, err
		}
		artifactNames := make([]string, 0, len(artifacts))
		for _, artifact := range artifacts {
			artifactNames = append(artifactNames, artifact.Name)
		}
		observation, _ := json.Marshal(map[string]any{
			"executable": filepath.Base(executable), "artifacts": artifactNames,
		})
		result.Artifacts = artifacts
		result.Observations = append(result.Observations, ObservationResult{
			TechniqueCode: manifest.Spec.Techniques[0].Code, Kind: "command.completed", Data: string(observation),
		})
		return result, nil
	}
}

func materializeWordlists(specs []model.PluginInput, inputs map[string]any, directory, workDir string) (map[string]any, error) {
	result := make(map[string]any, len(inputs))
	for name, value := range inputs {
		result[name] = value
	}
	for _, spec := range specs {
		if spec.Type != "wordlist" {
			continue
		}
		if _, ok := result[spec.Name]; !ok {
			continue
		}
		name, ok := result[spec.Name].(string)
		if !ok {
			return nil, fmt.Errorf("wordlist input %q is not a string", spec.Name)
		}
		path, err := copyWordlist(directory, name, workDir, spec)
		if err != nil {
			return nil, fmt.Errorf("wordlist input %q: %w", spec.Name, err)
		}
		result[spec.Name] = path
	}
	return result, nil
}

func copyWordlist(directory, name, workDir string, spec model.PluginInput) (string, error) {
	if name == "" || filepath.IsAbs(name) || filepath.Clean(name) != name || strings.Contains(name, string(filepath.Separator)) {
		return "", errors.New("must name one file in the configured wordlist directory")
	}
	root, err := os.OpenRoot(directory)
	if err != nil {
		return "", fmt.Errorf("open wordlist directory: %w", err)
	}
	defer root.Close()
	info, err := root.Lstat(name)
	if err != nil {
		return "", fmt.Errorf("inspect %q: %w", name, err)
	}
	if !info.Mode().IsRegular() {
		return "", fmt.Errorf("%q is not a regular file", name)
	}
	input, err := root.Open(name)
	if err != nil {
		return "", fmt.Errorf("open %q: %w", name, err)
	}
	defer input.Close()
	info, err = input.Stat()
	if err != nil {
		return "", fmt.Errorf("inspect %q: %w", name, err)
	}
	if !info.Mode().IsRegular() {
		return "", fmt.Errorf("%q is not a regular file", name)
	}
	if info.Size() > spec.MaximumBytes {
		return "", fmt.Errorf("%q exceeds %d bytes", name, spec.MaximumBytes)
	}
	data, err := io.ReadAll(io.LimitReader(input, spec.MaximumBytes+1))
	if err != nil {
		return "", fmt.Errorf("read %q: %w", name, err)
	}
	if int64(len(data)) > spec.MaximumBytes {
		return "", fmt.Errorf("%q exceeds %d bytes", name, spec.MaximumBytes)
	}
	if !utf8.Valid(data) || bytes.IndexByte(data, 0) >= 0 {
		return "", fmt.Errorf("%q must contain UTF-8 text without NUL bytes", name)
	}
	scanner := bufio.NewScanner(bytes.NewReader(data))
	scanner.Buffer(make([]byte, 1024), maxWordlistLine+2)
	lines := 0
	for scanner.Scan() {
		lines++
		if lines > spec.MaximumLines {
			return "", fmt.Errorf("%q exceeds %d lines", name, spec.MaximumLines)
		}
		if len(scanner.Bytes()) > maxWordlistLine {
			return "", fmt.Errorf("%q contains a line exceeding %d bytes", name, maxWordlistLine)
		}
	}
	if err := scanner.Err(); err != nil {
		return "", fmt.Errorf("read %q: %w", name, err)
	}
	outputPath := filepath.Join(workDir, "input-"+spec.Name+".txt")
	output, err := os.OpenFile(outputPath, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
	if err != nil {
		return "", fmt.Errorf("create task wordlist: %w", err)
	}
	_, writeErr := output.Write(data)
	closeErr := output.Close()
	if writeErr != nil {
		return "", fmt.Errorf("copy %q: %w", name, writeErr)
	}
	if closeErr != nil {
		return "", fmt.Errorf("close task wordlist: %w", closeErr)
	}
	return outputPath, nil
}

func commandArgs(spec *CommandSpec, target, workDir string, inputs map[string]any) ([]string, error) {
	artifacts := make(map[string]string, len(spec.Artifacts))
	for _, artifact := range spec.Artifacts {
		artifacts[artifact.Name] = filepath.Join(workDir, artifact.Name)
	}
	return expandArguments(spec.Args, target, artifacts, inputs)
}

func expandArguments(arguments []string, target string, artifacts map[string]string, inputs map[string]any) ([]string, error) {
	result := make([]string, 0, len(arguments))
	for _, argument := range arguments {
		switch {
		case argument == "{{target}}":
			result = append(result, target)
		case argument == "{{target.host}}":
			host, err := targetHost(target)
			if err != nil {
				return nil, err
			}
			result = append(result, host)
		case strings.HasPrefix(argument, "{{artifact:") && strings.HasSuffix(argument, "}}"):
			name := strings.TrimSuffix(strings.TrimPrefix(argument, "{{artifact:"), "}}")
			path, ok := artifacts[name]
			if !ok {
				return nil, fmt.Errorf("argument references undeclared artifact %q", name)
			}
			result = append(result, path)
		case strings.HasPrefix(argument, "{{input:") && strings.HasSuffix(argument, "}}"):
			name := strings.TrimSuffix(strings.TrimPrefix(argument, "{{input:"), "}}")
			value, ok := inputs[name]
			if !ok {
				return nil, fmt.Errorf("argument references unresolved input %q", name)
			}
			text, err := inputArgument(value)
			if err != nil {
				return nil, fmt.Errorf("input %q: %w", name, err)
			}
			result = append(result, text)
		default:
			result = append(result, argument)
		}
	}
	return result, nil
}

func targetHost(target string) (string, error) {
	parsed, err := url.Parse(target)
	if err != nil || parsed.Scheme == "" || parsed.Hostname() == "" {
		return "", fmt.Errorf("target %q is not an absolute URL", target)
	}
	return parsed.Hostname(), nil
}

func commandEnvironment(request Request, workDir string) []string {
	keys := []string{"HOME", "PATH", "TMPDIR", "SSL_CERT_DIR", "SSL_CERT_FILE"}
	environment := make([]string, 0, len(keys)+3)
	for _, key := range keys {
		if value, ok := os.LookupEnv(key); ok {
			environment = append(environment, key+"="+value)
		}
	}
	return append(environment,
		"OWTF_TARGET="+request.Target.Value,
		"OWTF_TARGET_KIND="+request.Target.Kind,
		"OWTF_ARTIFACT_DIR="+workDir,
	)
}

func readCommandArtifacts(workDir string, specs []CommandArtifact) ([]ArtifactResult, error) {
	root, err := os.OpenRoot(workDir)
	if err != nil {
		return nil, fmt.Errorf("open artifact directory: %w", err)
	}
	defer root.Close()

	result := make([]ArtifactResult, 0, len(specs))
	for _, spec := range specs {
		file, err := root.Open(spec.Name)
		if os.IsNotExist(err) && !spec.Required {
			continue
		}
		if err != nil {
			return nil, fmt.Errorf("open artifact %s: %w", spec.Name, err)
		}
		info, err := file.Stat()
		if err != nil {
			file.Close()
			return nil, fmt.Errorf("inspect artifact %s: %w", spec.Name, err)
		}
		if !info.Mode().IsRegular() {
			file.Close()
			return nil, fmt.Errorf("artifact %s is not a regular file", spec.Name)
		}
		data, readErr := io.ReadAll(io.LimitReader(file, maxArtifactSize+1))
		closeErr := file.Close()
		if readErr != nil {
			return nil, fmt.Errorf("read artifact %s: %w", spec.Name, readErr)
		}
		if closeErr != nil {
			return nil, fmt.Errorf("close artifact %s: %w", spec.Name, closeErr)
		}
		if len(data) > maxArtifactSize {
			return nil, fmt.Errorf("artifact %s exceeds 10 MiB", spec.Name)
		}
		result = append(result, ArtifactResult{Name: spec.Name, MediaType: spec.MediaType, Data: data})
	}
	return result, nil
}

func supportsTarget(kinds []string, kind string) bool {
	if len(kinds) == 0 {
		return true
	}
	for _, candidate := range kinds {
		if candidate == kind {
			return true
		}
	}
	return false
}

func formatCommand(executable string, args []string) string {
	parts := []string{strconv.Quote(executable)}
	for _, arg := range args {
		parts = append(parts, strconv.Quote(arg))
	}
	return strings.Join(parts, " ")
}

type eventWriter struct {
	stream    string
	log       func(string, string)
	remaining int
	pending   []byte
	events    int
	truncated bool
}

func (w *eventWriter) Write(data []byte) (int, error) {
	original := len(data)
	if w.remaining <= 0 || w.events >= maxLogEvents {
		w.truncated = true
		return original, nil
	}
	if len(data) > w.remaining {
		data = data[:w.remaining]
		w.truncated = true
	}
	w.remaining -= len(data)
	w.pending = append(w.pending, data...)
	for w.events < maxLogEvents {
		index := bytes.IndexByte(w.pending, '\n')
		if index < 0 {
			break
		}
		w.emit(string(w.pending[:index]))
		w.pending = w.pending[index+1:]
	}
	return original, nil
}

func (w *eventWriter) Close() {
	if len(w.pending) > 0 && w.events < maxLogEvents {
		w.emit(string(w.pending))
	}
	if w.truncated {
		w.log("system", w.stream+" truncated")
	}
}

func (w *eventWriter) emit(line string) {
	w.events++
	if line = strings.TrimSpace(line); line != "" {
		w.log(w.stream, line)
	}
}
