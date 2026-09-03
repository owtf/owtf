package plugin

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path"
	"strings"
	"time"
)

const containerArtifactDir = "/owtf/artifacts"

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
}

// ContainerEngine executes a plugin image without giving the plugin access to
// OWTF internals or the container engine socket.
type ContainerEngine interface {
	ImageAvailable(context.Context, string) error
	Run(context.Context, ContainerRun, io.Writer, io.Writer) error
}

// ContainerExecutor returns an executor for a validated container manifest.
// Networking is disabled by the engine until OWTF supplies a captured egress
// path; this prevents container plugins from silently bypassing transactions.
func ContainerExecutor(manifest Manifest, engine ContainerEngine) Executor {
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
		args, err := containerArgs(spec, request.Target.Value, request.Inputs)
		if err != nil {
			return Result{}, err
		}
		request.Log("system", "container "+spec.Image+" "+formatCommand(spec.Executable, args))
		stdout := &eventWriter{stream: "stdout", log: request.Log, remaining: maxCommandOutput}
		stderr := &eventWriter{stream: "stderr", log: request.Log, remaining: maxCommandOutput}
		err = engine.Run(ctx, ContainerRun{
			TaskID: request.TaskID, PluginID: request.PluginID,
			Image: spec.Image, Executable: spec.Executable, Args: args,
			Environment: containerEnvironment(request), ArtifactDir: workDir,
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
		artifactNames := make([]string, 0, len(artifacts))
		for _, artifact := range artifacts {
			artifactNames = append(artifactNames, artifact.Name)
		}
		return Result{
			Artifacts: artifacts,
			Observations: []ObservationResult{{
				TechniqueCode: manifest.Spec.Techniques[0], Kind: "container.completed",
				Data: containerObservation(spec, artifactNames),
			}},
		}, nil
	}
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
		"image": spec.Image, "executable": path.Base(spec.Executable), "artifacts": artifacts,
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

// Run creates one network-disabled container, attaches its logs, copies its
// declared output directory, and forcibly removes it on every exit path.
func (e *DockerEngine) Run(ctx context.Context, run ContainerRun, stdout, stderr io.Writer) error {
	if err := os.MkdirAll(run.ArtifactDir, 0o700); err != nil {
		return fmt.Errorf("create artifact directory: %w", err)
	}
	args := []string{
		"create", "--pull", "never", "--init",
		"--network", "none", "--read-only", "--cap-drop", "ALL",
		"--security-opt", "no-new-privileges", "--pids-limit", "256",
		"--memory", "512m", "--cpus", "1",
		"--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=67108864",
		"--tmpfs", containerArtifactDir + ":rw,nosuid,nodev,size=67108864",
		"--label", "dev.owtf.task=" + run.TaskID,
		"--label", "dev.owtf.plugin=" + run.PluginID,
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
	if _, err := e.output(ctx, "cp", containerID+":"+containerArtifactDir+"/.", run.ArtifactDir); err != nil {
		return fmt.Errorf("copy container artifacts: %w", err)
	}
	return nil
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
