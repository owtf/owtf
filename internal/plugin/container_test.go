//go:build !windows

package plugin

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"testing/fstest"
	"time"

	"github.com/owtf/owtf/internal/model"
)

func TestContainerExecutorPreservesArgumentsAndCollectsArtifacts(t *testing.T) {
	manifest := containerManifest()
	engine := &fakeContainerEngine{run: func(run ContainerRun) error {
		if run.Image != "example.test/owtf/plugin@sha256:abc" {
			t.Fatalf("image = %q", run.Image)
		}
		wantArgs := []string{"--url", "https://example.test/; touch /tmp/injected", "/owtf/artifacts/result.json"}
		if !reflect.DeepEqual(run.Args, wantArgs) {
			t.Fatalf("args = %#v, want %#v", run.Args, wantArgs)
		}
		if !reflect.DeepEqual(run.Artifacts, []string{"result.json"}) {
			t.Fatalf("artifacts = %#v", run.Artifacts)
		}
		if err := os.WriteFile(filepath.Join(run.ArtifactDir, "result.json"), []byte(`{"ok":true}`), 0o600); err != nil {
			return err
		}
		return nil
	}}
	var events []string
	result, err := ContainerExecutor(manifest, engine, t.TempDir())(context.Background(), Request{
		TaskID: "task-1", PluginID: manifest.Metadata.ID,
		Target: model.Target{Kind: "url", Value: "https://example.test/; touch /tmp/injected"},
		Log:    func(stream, message string) { events = append(events, stream+":"+message) },
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Artifacts) != 1 || string(result.Artifacts[0].Data) != `{"ok":true}` {
		t.Fatalf("artifacts = %+v", result.Artifacts)
	}
	if len(events) != 1 || !strings.Contains(events[0], "container example.test/owtf/plugin") {
		t.Fatalf("events = %#v", events)
	}
}

func TestContainerArtifactArchiveRoundTrip(t *testing.T) {
	source := t.TempDir()
	want := []byte(`{"ok":true}`)
	if err := os.WriteFile(filepath.Join(source, "result.json"), want, 0o600); err != nil {
		t.Fatal(err)
	}
	archive, err := archiveContainerInputs(source)
	if err != nil {
		t.Fatal(err)
	}
	destination := t.TempDir()
	if err := extractContainerArtifacts(bytes.NewReader(archive), destination, []string{"result.json"}); err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(filepath.Join(destination, "result.json"))
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("artifact = %q, want %q", got, want)
	}
}

func TestContainerDecoderFailureRetainsRawArtifact(t *testing.T) {
	manifest := containerManifest()
	manifest.Spec.Runtime.Container.Artifacts[0].Decoder = "nmap-xml"
	engine := &fakeContainerEngine{run: func(run ContainerRun) error {
		return os.WriteFile(filepath.Join(run.ArtifactDir, "result.json"), []byte("<nmaprun>"), 0o600)
	}}
	result, err := ContainerExecutor(manifest, engine, t.TempDir())(context.Background(), Request{
		TaskID: "task-1", Target: model.Target{Kind: "url", Value: "https://example.test"}, Log: func(string, string) {},
	})
	if err == nil || !strings.Contains(err.Error(), "decode artifact") {
		t.Fatalf("decoder failure was hidden: %v", err)
	}
	if len(result.Artifacts) != 1 || string(result.Artifacts[0].Data) != "<nmaprun>" || len(result.Observations) != 0 {
		t.Fatalf("raw evidence was discarded or completion fabricated: %+v", result)
	}
}

func TestContainerArtifactArchiveRejectsUndeclaredFile(t *testing.T) {
	source := t.TempDir()
	if err := os.WriteFile(filepath.Join(source, "unexpected.json"), []byte("{}"), 0o600); err != nil {
		t.Fatal(err)
	}
	archive, err := archiveContainerInputs(source)
	if err != nil {
		t.Fatal(err)
	}
	err = extractContainerArtifacts(bytes.NewReader(archive), t.TempDir(), []string{"result.json"})
	if err == nil || !strings.Contains(err.Error(), "undeclared artifact") {
		t.Fatalf("error = %v", err)
	}
}

func TestContainerExecutorMaterializesWordlistAndDecodesArtifact(t *testing.T) {
	manifest := containerManifest()
	manifest.Spec.Inputs = []model.PluginInput{{
		Name: "wordlist", Type: "wordlist", Required: true,
		MaximumBytes: 64, MaximumLines: 2,
	}}
	manifest.Spec.Runtime.Container.Network = "bridge"
	manifest.Spec.Runtime.Container.Args = []string{
		"--wordlist", "{{input:wordlist}}", "--output", "{{artifact:urls.txt}}",
	}
	manifest.Spec.Runtime.Container.Artifacts = []CommandArtifact{{
		Name: "urls.txt", MediaType: "text/plain", Required: true, Decoder: "url-list",
	}}
	wordlists := t.TempDir()
	if err := os.WriteFile(filepath.Join(wordlists, "small.txt"), []byte("admin\napi\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	engine := &fakeContainerEngine{run: func(run ContainerRun) error {
		if run.Network != "bridge" || run.InputDir == "" {
			t.Fatalf("run network/input directory = %q/%q", run.Network, run.InputDir)
		}
		wantArgs := []string{"--wordlist", "/owtf/inputs/input-wordlist.txt", "--output", "/owtf/artifacts/urls.txt"}
		if !reflect.DeepEqual(run.Args, wantArgs) {
			t.Fatalf("args = %#v, want %#v", run.Args, wantArgs)
		}
		data, err := os.ReadFile(filepath.Join(run.InputDir, "input-wordlist.txt"))
		if err != nil || string(data) != "admin\napi\n" {
			t.Fatalf("materialized wordlist = %q, %v", data, err)
		}
		return os.WriteFile(filepath.Join(run.ArtifactDir, "urls.txt"), []byte("https://example.test/admin\n"), 0o600)
	}}
	result, err := ContainerExecutor(manifest, engine, wordlists)(context.Background(), Request{
		TaskID: "task-1", PluginID: manifest.Metadata.ID,
		Target: model.Target{Kind: "url", Value: "https://example.test/"},
		Inputs: map[string]any{"wordlist": "small.txt"}, Log: func(string, string) {},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Artifacts) != 1 || len(result.URLs) != 1 || result.URLs[0].URL != "https://example.test/admin" {
		t.Fatalf("result = %+v", result)
	}
	if got := result.Observations[len(result.Observations)-1].Kind; got != "container.completed" {
		t.Fatalf("last observation kind = %q", got)
	}
}

func TestResolveContainersReportsImageAvailability(t *testing.T) {
	catalog, err := Load(fstest.MapFS{"plugin.yaml": &fstest.MapFile{Data: []byte(containerManifestYAML())}})
	if err != nil {
		t.Fatal(err)
	}
	catalog.ResolveContainers(context.Background(), &fakeContainerEngine{available: errors.New("not found")}, t.TempDir())
	entry, _ := catalog.Get("OWTF-TEST-001-active")
	if entry.Availability != "missing_requirements" || entry.Executor != nil || !strings.Contains(entry.Reason, "not found") {
		t.Fatalf("entry = %+v", entry)
	}

	catalog.ResolveContainers(context.Background(), &fakeContainerEngine{}, t.TempDir())
	entry, _ = catalog.Get("OWTF-TEST-001-active")
	if entry.Availability != "ready" || entry.Executor == nil || entry.Reason != "" {
		t.Fatalf("entry = %+v", entry)
	}
}

func TestDockerEngineForcesRemovalAfterCancellation(t *testing.T) {
	logPath := filepath.Join(t.TempDir(), "docker.log")
	engine := &DockerEngine{command: func(ctx context.Context, args ...string) *exec.Cmd {
		helperArgs := append([]string{"-test.run=TestDockerCommandHelper", "--"}, args...)
		command := exec.CommandContext(ctx, os.Args[0], helperArgs...)
		command.Env = append(os.Environ(), "OWTF_DOCKER_LOG="+logPath)
		return command
	}}

	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	artifactDir := t.TempDir()
	go func() {
		done <- engine.Run(ctx, ContainerRun{
			TaskID: "task-1", PluginID: "OWTF-TEST-001-active", Image: "plugin:test",
			Executable: "/bin/plugin", Args: []string{"https://example.test"}, ArtifactDir: artifactDir,
			Artifacts: []string{"result.json"},
		}, os.Stdout, os.Stderr)
	}()
	waitForFileText(t, logPath, "start --attach container-id")
	cancel()
	select {
	case err := <-done:
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("Run error = %v", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("container run did not stop")
	}
	waitForFileText(t, logPath, "rm --force --volumes container-id")
	waitForFileText(t, logPath, "volume rm --force volume-id")
	data, err := os.ReadFile(logPath)
	if err != nil {
		t.Fatal(err)
	}
	log := string(data)
	for _, want := range []string{
		"create --pull never --init --network none --read-only",
		"--label dev.owtf.task=task-1",
		"--label dev.owtf.plugin=OWTF-TEST-001-active",
		"--entrypoint /bin/plugin plugin:test https://example.test",
	} {
		if !strings.Contains(log, want) {
			t.Fatalf("docker log does not contain %q:\n%s", want, log)
		}
	}
}

func TestDockerEngineRemovesInputHelperAfterCancellation(t *testing.T) {
	logPath := filepath.Join(t.TempDir(), "docker.log")
	engine := &DockerEngine{command: func(ctx context.Context, args ...string) *exec.Cmd {
		helperArgs := append([]string{"-test.run=TestDockerCommandHelper", "--"}, args...)
		command := exec.CommandContext(ctx, os.Args[0], helperArgs...)
		command.Env = append(os.Environ(), "OWTF_DOCKER_LOG="+logPath)
		return command
	}}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	done := make(chan error, 1)
	run := ContainerRun{TaskID: "task-1", Image: "plugin:test", InputDir: t.TempDir(), ArtifactDir: t.TempDir()}
	go func() { done <- engine.Run(ctx, run, io.Discard, io.Discard) }()
	waitForFileText(t, logPath, "start --attach --interactive container-id")
	cancel()
	select {
	case err := <-done:
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("Run error = %v", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("input helper did not stop")
	}
	waitForFileText(t, logPath, "rm --force --volumes container-id")
	waitForFileText(t, logPath, "volume rm --force volume-id")
}

func TestDockerCommandHelper(t *testing.T) {
	separator := -1
	for index, arg := range os.Args {
		if arg == "--" {
			separator = index
			break
		}
	}
	if separator < 0 || separator+1 >= len(os.Args) || os.Getenv("OWTF_DOCKER_LOG") == "" {
		return
	}
	args := os.Args[separator+1:]
	file, err := os.OpenFile(os.Getenv("OWTF_DOCKER_LOG"), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o600)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	_, _ = fmt.Fprintln(file, strings.Join(args, " "))
	_ = file.Close()
	switch args[0] {
	case "volume":
		if args[1] == "create" {
			fmt.Println("volume-id")
		}
		os.Exit(0)
	case "create":
		fmt.Println("container-id")
		os.Exit(0)
	case "start":
		for {
			time.Sleep(time.Hour)
		}
	default:
		os.Exit(0)
	}
}

type fakeContainerEngine struct {
	available error
	run       func(ContainerRun) error
}

func (e *fakeContainerEngine) ImageAvailable(context.Context, string) error { return e.available }
func (e *fakeContainerEngine) Run(_ context.Context, run ContainerRun, _, _ io.Writer) error {
	if e.run == nil {
		return nil
	}
	return e.run(run)
}

func containerManifest() Manifest {
	var manifest Manifest
	manifest.Metadata.ID = "OWTF-TEST-001-active"
	manifest.Spec.Techniques = []TechniqueSpec{{Code: "OWTF-TEST-001", Title: "Test", Priority: 99}}
	manifest.Spec.TargetKinds = []string{"url"}
	manifest.Spec.Runtime.Type = "container"
	manifest.Spec.Runtime.Container = &ContainerSpec{
		Image: "example.test/owtf/plugin@sha256:abc", Executable: "/bin/plugin",
		Args:      []string{"--url", "{{target}}", "{{artifact:result.json}}"},
		Artifacts: []CommandArtifact{{Name: "result.json", MediaType: "application/json", Required: true}},
	}
	return manifest
}

func containerManifestYAML() string {
	return `apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-TEST-001-active
  version: 0.1.0
  title: Container test
spec:
  techniques: [OWTF-TEST-001]
  group: web
  type: active
  runtime:
    type: container
    container:
      image: example.test/owtf/plugin@sha256:abc
      executable: /bin/plugin
      args: [--url, '{{target}}']
`
}

func waitForFileText(t *testing.T, path, want string) {
	t.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for {
		data, _ := os.ReadFile(path)
		if strings.Contains(string(data), want) {
			return
		}
		if time.Now().After(deadline) {
			t.Fatalf("%q was not written to %s", want, path)
		}
		time.Sleep(10 * time.Millisecond)
	}
}
