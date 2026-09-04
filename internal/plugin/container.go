package plugin

import (
	"archive/tar"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"strings"
	"time"
)

const (
	containerArtifactDir      = "/owtf/artifacts"
	containerInputDir         = "/owtf/inputs"
	maxContainerInputBytes    = 32 << 20
	maxContainerArtifactBytes = 32 << 20
)

// ContainerRun is the complete input passed to a container engine. The engine
// must remove the container when Run returns, including after cancellation.
type ContainerRun struct {
	TaskID      string
	PluginID    string
	Image       string
	Executable  string
	Args        []string
	Environment []string
	ArtifactDir string
	Artifacts   []string
	InputDir    string
	Network     string
}

// ContainerEngine executes a plugin image without giving the plugin access to
// OWTF internals or the container engine socket.
type ContainerEngine interface {
	ImageAvailable(context.Context, string) error
	Run(context.Context, ContainerRun, io.Writer, io.Writer) error
}

// ContainerExecutor returns an executor for a validated container manifest.
func ContainerExecutor(manifest Manifest, engine ContainerEngine, wordlistDirectory string) Executor {
	return func(ctx context.Context, request Request) (Result, error) {
		if !supportsTarget(manifest.Spec.TargetKinds, request.Target.Kind) {
			return Result{}, fmt.Errorf("plugin does not support %s targets", request.Target.Kind)
		}
		if engine == nil {
			return Result{}, fmt.Errorf("container engine is not configured")
		}
		workDir, err := os.MkdirTemp("", "owtf-plugin-container-*")
		if err != nil {
			return Result{}, fmt.Errorf("create plugin directory: %w", err)
		}
		defer os.RemoveAll(workDir)

		spec := manifest.Spec.Runtime.Container
		inputs, inputDir, err := containerInputs(manifest, request.Inputs, wordlistDirectory, workDir)
		if err != nil {
			return Result{}, err
		}
		args, err := containerArgs(spec, request.Target.Value, inputs)
		if err != nil {
			return Result{}, err
		}
		request.Log("system", "container "+spec.Image+" "+formatCommand(spec.Executable, args))
		stdout := &eventWriter{stream: "stdout", log: request.Log, remaining: maxCommandOutput, errorPrefix: spec.ErrorPrefix}
		stderr := &eventWriter{stream: "stderr", log: request.Log, remaining: maxCommandOutput, errorPrefix: spec.ErrorPrefix}
		declaredArtifacts := make([]string, 0, len(spec.Artifacts))
		for _, artifact := range spec.Artifacts {
			declaredArtifacts = append(declaredArtifacts, artifact.Name)
		}
		err = engine.Run(ctx, ContainerRun{
			TaskID: request.TaskID, PluginID: request.PluginID,
			Image: spec.Image, Executable: spec.Executable, Args: args,
			Environment: containerEnvironment(request), ArtifactDir: workDir,
			Artifacts: declaredArtifacts, InputDir: inputDir, Network: spec.Network,
		}, stdout, stderr)
		stdout.Close()
		stderr.Close()
		if err != nil {
			return Result{}, fmt.Errorf("container failed: %w", err)
		}

		artifacts, err := readCommandArtifacts(workDir, spec.Artifacts)
		if err != nil {
			return Result{}, err
		}
		if stdout.outputFailed() || stderr.outputFailed() {
			return Result{Artifacts: artifacts}, fmt.Errorf("container output reported errors or was truncated; see task logs")
		}
		result, err := decodeArtifacts(manifest, request.Target, artifacts)
		if err != nil {
			return Result{Artifacts: artifacts}, err
		}
		artifactNames := make([]string, 0, len(artifacts))
		for _, artifact := range artifacts {
			artifactNames = append(artifactNames, artifact.Name)
		}
		result.Artifacts = artifacts
		result.Observations = append(result.Observations, ObservationResult{
			TechniqueCode: manifest.Spec.Techniques[0].Code, Kind: "container.completed",
			Data: containerObservation(spec, artifactNames),
		})
		return result, nil
	}
}

func containerInputs(manifest Manifest, inputs map[string]any, wordlistDirectory, workDir string) (map[string]any, string, error) {
	hasWordlist := false
	for _, input := range manifest.Spec.Inputs {
		if input.Type == "wordlist" {
			hasWordlist = true
			break
		}
	}
	if !hasWordlist {
		return inputs, "", nil
	}
	inputDir := filepath.Join(workDir, "inputs")
	if err := os.Mkdir(inputDir, 0o700); err != nil {
		return nil, "", fmt.Errorf("create container input directory: %w", err)
	}
	result, err := materializeWordlists(manifest.Spec.Inputs, inputs, wordlistDirectory, inputDir)
	if err != nil {
		return nil, "", err
	}
	for _, input := range manifest.Spec.Inputs {
		if input.Type != "wordlist" {
			continue
		}
		if _, ok := result[input.Name]; !ok {
			continue
		}
		hostPath, ok := result[input.Name].(string)
		if !ok {
			return nil, "", fmt.Errorf("wordlist input %q is not a string", input.Name)
		}
		result[input.Name] = path.Join(containerInputDir, filepath.Base(hostPath))
	}
	return result, inputDir, nil
}

func containerArgs(spec *ContainerSpec, target string, inputs map[string]any) ([]string, error) {
	artifacts := make(map[string]string, len(spec.Artifacts))
	for _, artifact := range spec.Artifacts {
		artifacts[artifact.Name] = path.Join(containerArtifactDir, artifact.Name)
	}
	return expandArguments(spec.Args, target, artifacts, inputs)
}

func containerEnvironment(request Request) []string {
	return []string{
		"HOME=/tmp",
		"OWTF_ARTIFACT_DIR=" + containerArtifactDir,
		"OWTF_PLUGIN_ID=" + request.PluginID,
		"OWTF_TARGET=" + request.Target.Value,
		"OWTF_TARGET_KIND=" + request.Target.Kind,
		"OWTF_TASK_ID=" + request.TaskID,
	}
}

func containerObservation(spec *ContainerSpec, artifacts []string) string {
	data, _ := json.Marshal(map[string]any{
		"image": spec.Image, "executable": path.Base(spec.Executable), "network": containerNetwork(spec.Network), "artifacts": artifacts,
	})
	return string(data)
}

// DockerEngine uses the Docker CLI as a narrow engine adapter. It never pulls
// images and never uses shell command strings.
type DockerEngine struct {
	command func(context.Context, ...string) *exec.Cmd
}

// NewDockerEngine creates an adapter for docker or a compatible CLI path.
func NewDockerEngine(executable string) *DockerEngine {
	if strings.TrimSpace(executable) == "" {
		executable = "docker"
	}
	return &DockerEngine{command: func(ctx context.Context, args ...string) *exec.Cmd {
		return exec.CommandContext(ctx, executable, args...)
	}}
}

// ImageAvailable verifies that an image already exists in the local engine.
func (e *DockerEngine) ImageAvailable(ctx context.Context, image string) error {
	if _, err := e.output(ctx, "image", "inspect", image); err != nil {
		return fmt.Errorf("container image %q is unavailable: %w", image, err)
	}
	return nil
}

// Run creates one resource-bounded container, attaches its logs, exports only
// declared artifacts, and forcibly removes its resources on every exit path.
func (e *DockerEngine) Run(ctx context.Context, run ContainerRun, stdout, stderr io.Writer) error {
	if err := os.MkdirAll(run.ArtifactDir, 0o700); err != nil {
		return fmt.Errorf("create artifact directory: %w", err)
	}
	network := containerNetwork(run.Network)
	if network != "none" && network != "bridge" {
		return fmt.Errorf("unsupported container network %q", run.Network)
	}
	inputVolume, err := e.createInputVolume(ctx, run)
	if err != nil {
		return err
	}
	if inputVolume != "" {
		defer e.removeVolume(inputVolume)
	}
	artifactVolume := ""
	if len(run.Artifacts) != 0 {
		artifactVolume, err = e.createTaskVolume(ctx, run.TaskID, "artifacts")
		if err != nil {
			return err
		}
		defer e.removeVolume(artifactVolume)
	}
	args := []string{
		"create", "--pull", "never", "--init",
		"--network", network, "--read-only", "--cap-drop", "ALL",
		"--security-opt", "no-new-privileges", "--pids-limit", "256",
		"--memory", "512m", "--cpus", "1",
		"--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=67108864",
		"--label", "dev.owtf.task=" + run.TaskID,
		"--label", "dev.owtf.plugin=" + run.PluginID,
	}
	if network == "bridge" {
		args = append(args, "--add-host", "host.docker.internal:host-gateway")
	}
	if inputVolume != "" {
		args = append(args, "--mount", "type=volume,src="+inputVolume+",dst="+containerInputDir+",readonly")
	}
	if artifactVolume != "" {
		args = append(args, "--mount", "type=volume,src="+artifactVolume+",dst="+containerArtifactDir)
	} else {
		args = append(args, "--tmpfs", containerArtifactDir+":rw,nosuid,nodev,size=67108864")
	}
	for _, value := range run.Environment {
		args = append(args, "--env", value)
	}
	args = append(args, "--entrypoint", run.Executable, run.Image)
	args = append(args, run.Args...)

	containerID, err := e.output(ctx, args...)
	if err != nil {
		return fmt.Errorf("create container: %w", err)
	}
	containerID = strings.TrimSpace(containerID)
	if fields := strings.Fields(containerID); len(fields) == 1 {
		containerID = fields[0]
	} else {
		return fmt.Errorf("create container returned an invalid ID")
	}
	defer e.remove(containerID)

	command := e.command(ctx, "start", "--attach", containerID)
	command.Stdout = stdout
	command.Stderr = stderr
	if err := command.Run(); err != nil {
		if ctx.Err() != nil {
			return ctx.Err()
		}
		return fmt.Errorf("start container: %w", err)
	}
	if artifactVolume != "" {
		if err := e.extractArtifactVolume(ctx, run, artifactVolume); err != nil {
			return err
		}
	}
	return nil
}

func (e *DockerEngine) createInputVolume(ctx context.Context, run ContainerRun) (string, error) {
	if run.InputDir == "" {
		return "", nil
	}
	archive, err := archiveContainerInputs(run.InputDir)
	if err != nil {
		return "", err
	}
	volume, err := e.createTaskVolume(ctx, run.TaskID, "inputs")
	if err != nil {
		return "", err
	}
	helperID, err := e.createVolumeHelper(ctx, run, volume, containerInputDir, false, "-x", "-C", containerInputDir)
	if err != nil {
		e.removeVolume(volume)
		return "", err
	}
	populated := false
	defer func() {
		e.remove(helperID)
		if !populated {
			e.removeVolume(volume)
		}
	}()
	command := e.command(ctx, "start", "--attach", "--interactive", helperID)
	command.Stdin = bytes.NewReader(archive)
	output, err := command.CombinedOutput()
	if err != nil {
		if ctx.Err() != nil {
			return "", ctx.Err()
		}
		message := strings.TrimSpace(string(output))
		if message != "" {
			return "", fmt.Errorf("populate container input volume: %w: %s", err, message)
		}
		return "", fmt.Errorf("populate container input volume: %w", err)
	}
	populated = true
	return volume, nil
}

func (e *DockerEngine) createTaskVolume(ctx context.Context, taskID, kind string) (string, error) {
	volume, err := e.output(ctx, "volume", "create",
		"--label", "dev.owtf.task="+taskID,
		"--label", "dev.owtf.kind="+kind,
	)
	if err != nil {
		return "", fmt.Errorf("create container %s volume: %w", kind, err)
	}
	volume = strings.TrimSpace(volume)
	if fields := strings.Fields(volume); len(fields) != 1 {
		return "", fmt.Errorf("create container %s volume returned an invalid name", kind)
	}
	return volume, nil
}

func (e *DockerEngine) createVolumeHelper(ctx context.Context, run ContainerRun, volume, directory string, readOnly bool, tarArgs ...string) (string, error) {
	mount := "type=volume,src=" + volume + ",dst=" + directory
	if readOnly {
		mount += ",readonly"
	}
	args := []string{
		"create", "--interactive", "--pull", "never", "--network", "none", "--read-only",
		"--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "32",
		"--memory", "64m", "--cpus", "0.25",
		"--label", "dev.owtf.task=" + run.TaskID,
		"--mount", mount, "--entrypoint", "/bin/tar", run.Image,
	}
	output, err := e.output(ctx, append(args, tarArgs...)...)
	if err != nil {
		return "", fmt.Errorf("create container volume helper: %w", err)
	}
	fields := strings.Fields(output)
	if len(fields) != 1 {
		return "", fmt.Errorf("create container volume helper returned an invalid ID")
	}
	return fields[0], nil
}

func (e *DockerEngine) extractArtifactVolume(ctx context.Context, run ContainerRun, volume string) error {
	helperID, err := e.createVolumeHelper(ctx, run, volume, containerArtifactDir, true, "-c", "-C", containerArtifactDir, ".")
	if err != nil {
		return err
	}
	defer e.remove(helperID)
	command := e.command(ctx, "start", "--attach", helperID)
	stdout, err := command.StdoutPipe()
	if err != nil {
		return fmt.Errorf("open container artifact stream: %w", err)
	}
	var stderr bytes.Buffer
	command.Stderr = &stderr
	if err := command.Start(); err != nil {
		return fmt.Errorf("start container artifact export: %w", err)
	}
	extractErr := extractContainerArtifacts(stdout, run.ArtifactDir, run.Artifacts)
	if extractErr != nil {
		_ = stdout.Close()
		_ = command.Process.Kill()
	}
	waitErr := command.Wait()
	if extractErr != nil {
		return extractErr
	}
	if waitErr != nil {
		if ctx.Err() != nil {
			return ctx.Err()
		}
		message := strings.TrimSpace(stderr.String())
		if message != "" {
			return fmt.Errorf("export container artifacts: %w: %s", waitErr, message)
		}
		return fmt.Errorf("export container artifacts: %w", waitErr)
	}
	return nil
}

func extractContainerArtifacts(reader io.Reader, directory string, declared []string) error {
	allowed := make(map[string]bool, len(declared))
	for _, name := range declared {
		allowed[name] = true
	}
	archive := tar.NewReader(reader)
	var total int64
	for {
		header, err := archive.Next()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return fmt.Errorf("read container artifact archive: %w", err)
		}
		name := strings.TrimPrefix(header.Name, "./")
		if name == "" || name == "." {
			continue
		}
		if header.Typeflag != tar.TypeReg && header.Typeflag != tar.TypeRegA {
			return fmt.Errorf("container artifact %q is not a regular file", name)
		}
		if !validArtifactName(name) || !allowed[name] {
			return fmt.Errorf("container produced undeclared artifact %q", name)
		}
		if header.Size < 0 || header.Size > maxArtifactSize {
			return fmt.Errorf("artifact %s exceeds 10 MiB", name)
		}
		total += header.Size
		if total > maxContainerArtifactBytes {
			return fmt.Errorf("container artifacts exceed 32 MiB")
		}
		output, err := os.OpenFile(filepath.Join(directory, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
		if err != nil {
			return fmt.Errorf("create container artifact %q: %w", name, err)
		}
		_, copyErr := io.CopyN(output, archive, header.Size)
		closeErr := output.Close()
		if copyErr != nil {
			return fmt.Errorf("extract container artifact %q: %w", name, copyErr)
		}
		if closeErr != nil {
			return fmt.Errorf("close container artifact %q: %w", name, closeErr)
		}
	}
}

func archiveContainerInputs(directory string) ([]byte, error) {
	root, err := os.OpenRoot(directory)
	if err != nil {
		return nil, fmt.Errorf("open container input directory: %w", err)
	}
	defer root.Close()
	entries, err := os.ReadDir(directory)
	if err != nil {
		return nil, fmt.Errorf("read container input directory: %w", err)
	}
	var buffer bytes.Buffer
	archive := tar.NewWriter(&buffer)
	var total int64
	for _, entry := range entries {
		if !validArtifactName(entry.Name()) {
			archive.Close()
			return nil, fmt.Errorf("invalid container input name %q", entry.Name())
		}
		if entry.Type()&os.ModeSymlink != 0 {
			archive.Close()
			return nil, fmt.Errorf("container input %q is not a regular file", entry.Name())
		}
		file, err := root.Open(entry.Name())
		if err != nil {
			archive.Close()
			return nil, fmt.Errorf("open container input %q: %w", entry.Name(), err)
		}
		info, err := file.Stat()
		if err != nil {
			file.Close()
			archive.Close()
			return nil, fmt.Errorf("inspect container input %q: %w", entry.Name(), err)
		}
		if !info.Mode().IsRegular() {
			file.Close()
			archive.Close()
			return nil, fmt.Errorf("container input %q is not a regular file", entry.Name())
		}
		total += info.Size()
		if total > maxContainerInputBytes {
			file.Close()
			archive.Close()
			return nil, fmt.Errorf("container inputs exceed 32 MiB")
		}
		if err := archive.WriteHeader(&tar.Header{Name: entry.Name(), Mode: 0o400, Size: info.Size()}); err != nil {
			file.Close()
			archive.Close()
			return nil, fmt.Errorf("archive container input %q: %w", entry.Name(), err)
		}
		_, copyErr := io.Copy(archive, file)
		closeErr := file.Close()
		if copyErr != nil {
			archive.Close()
			return nil, fmt.Errorf("archive container input %q: %w", entry.Name(), copyErr)
		}
		if closeErr != nil {
			archive.Close()
			return nil, fmt.Errorf("close container input %q: %w", entry.Name(), closeErr)
		}
	}
	if err := archive.Close(); err != nil {
		return nil, fmt.Errorf("close container input archive: %w", err)
	}
	return buffer.Bytes(), nil
}

func containerNetwork(value string) string {
	if value == "" {
		return "none"
	}
	return value
}

func (e *DockerEngine) output(ctx context.Context, args ...string) (string, error) {
	data, err := e.command(ctx, args...).CombinedOutput()
	if err == nil {
		return string(data), nil
	}
	if ctx.Err() != nil {
		return "", ctx.Err()
	}
	message := strings.TrimSpace(string(data))
	if message == "" {
		return "", err
	}
	return "", fmt.Errorf("%w: %s", err, message)
}

func (e *DockerEngine) remove(containerID string) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_, _ = e.output(ctx, "rm", "--force", "--volumes", containerID)
}

func (e *DockerEngine) removeVolume(name string) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_, _ = e.output(ctx, "volume", "rm", "--force", name)
}
