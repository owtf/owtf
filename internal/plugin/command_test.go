//go:build !windows

package plugin

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"syscall"
	"testing"
	"time"

	"github.com/owtf/owtf/internal/model"
)

func TestMaterializeWordlist(t *testing.T) {
	directory := t.TempDir()
	if err := os.WriteFile(filepath.Join(directory, "paths.txt"), []byte("admin\nbackup\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	workDir := t.TempDir()
	spec := model.PluginInput{Name: "wordlist", Type: "wordlist", MaximumBytes: 32, MaximumLines: 2}
	inputs, err := materializeWordlists([]model.PluginInput{spec}, map[string]any{"wordlist": "paths.txt"}, directory, workDir)
	if err != nil {
		t.Fatal(err)
	}
	path, ok := inputs["wordlist"].(string)
	if !ok || filepath.Dir(path) != workDir {
		t.Fatalf("wordlist path = %#v", inputs["wordlist"])
	}
	data, err := os.ReadFile(path)
	if err != nil || string(data) != "admin\nbackup\n" {
		t.Fatalf("wordlist = %q, %v", data, err)
	}
}

func TestMaterializeWordlistRejectsUnsafeInput(t *testing.T) {
	directory := t.TempDir()
	if err := os.WriteFile(filepath.Join(directory, "large.txt"), []byte("one\ntwo\nthree\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	spec := model.PluginInput{Name: "wordlist", Type: "wordlist", MaximumBytes: 64, MaximumLines: 2}
	for name, value := range map[string]string{
		"absolute": filepath.Join(directory, "large.txt"),
		"nested":   "nested/list.txt",
		"lines":    "large.txt",
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := materializeWordlists([]model.PluginInput{spec}, map[string]any{"wordlist": value}, directory, t.TempDir()); err == nil {
				t.Fatal("unsafe wordlist was accepted")
			}
		})
	}
}

func TestWordlistContentLimits(t *testing.T) {
	for name, test := range map[string]struct {
		data  []byte
		limit int64
	}{
		"bytes": {[]byte("admin\n"), 5},
		"line":  {[]byte(strings.Repeat("x", maxWordlistLine+1)), maxWordlistLine + 1},
		"nul":   {[]byte("admin\x00\n"), 64},
		"utf8":  {[]byte{0xff, '\n'}, 64},
	} {
		t.Run(name, func(t *testing.T) {
			directory := t.TempDir()
			if err := os.WriteFile(filepath.Join(directory, "words.txt"), test.data, 0o600); err != nil {
				t.Fatal(err)
			}
			spec := model.PluginInput{Name: "wordlist", Type: "wordlist", MaximumBytes: test.limit, MaximumLines: 2}
			if _, err := copyWordlist(directory, "words.txt", t.TempDir(), spec); err == nil {
				t.Fatal("invalid wordlist was accepted")
			}
		})
	}
}

func TestCommandArgumentsDoNotInvokeAShell(t *testing.T) {
	spec := &CommandSpec{
		Args:      []string{"--url", "{{target}}", "--user-agent", "{{input:user_agent}}", "{{artifact:output}}"},
		Artifacts: []CommandArtifact{{Name: "output"}},
	}
	target := "https://example.test/; touch /tmp/owtf-injected"
	userAgent := "OWTF; $(touch /tmp/owtf-input-injected)"
	args, err := commandArgs(spec, target, t.TempDir(), map[string]any{"user_agent": userAgent})
	if err != nil {
		t.Fatal(err)
	}
	if len(args) != 5 || args[1] != target || args[3] != userAgent {
		t.Fatalf("dynamic values were not preserved as whole arguments: %#v", args)
	}
}

func TestCommandArgumentsResolveTargetHost(t *testing.T) {
	spec := &CommandSpec{Args: []string{"-d", "{{target.host}}"}}
	args, err := commandArgs(spec, "https://user:pass@www.example.com:8443/path", t.TempDir(), nil)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(args, []string{"-d", "www.example.com"}) {
		t.Fatalf("unexpected arguments: %#v", args)
	}

	if _, err := commandArgs(spec, "not-a-url", t.TempDir(), nil); err == nil {
		t.Fatal("expected a relative target to be rejected")
	}
}

func TestCommandArtifactsCannotEscapeTheirDirectory(t *testing.T) {
	directory := t.TempDir()
	outside := filepath.Join(t.TempDir(), "secret")
	if err := os.WriteFile(outside, []byte("secret"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, filepath.Join(directory, "result")); err != nil {
		t.Fatal(err)
	}
	_, err := readCommandArtifacts(directory, []CommandArtifact{{Name: "result", Required: true}})
	if err == nil {
		t.Fatal("artifact symlink outside the assigned directory was accepted")
	}
}

func TestOutputErrorPrefix(t *testing.T) {
	for _, test := range []struct {
		parts  []string
		limit  int
		failed bool
	}{
		{[]string{"normal output\n"}, 100, false},
		{[]string{"[ER", "ROR] resolver failed"}, 100, true},
		{[]string{"  [ERROR] lookup failed\n"}, 100, true},
		{[]string{"more than ten bytes\n"}, 10, true},
		{[]string{strings.Repeat("ok\n", maxLogEvents) + "[ERROR] lookup failed\n"}, 10000, true},
	} {
		writer := &eventWriter{stream: "stdout", log: func(string, string) {}, remaining: test.limit, errorPrefix: "[ERROR]"}
		for _, part := range test.parts {
			if _, err := writer.Write([]byte(part)); err != nil {
				t.Fatal(err)
			}
		}
		writer.Close()
		if writer.outputFailed() != test.failed {
			t.Errorf("output %q failed=%v, want %v", test.parts, writer.outputFailed(), test.failed)
		}
	}
}

func TestCommandOutputErrorRetainsArtifacts(t *testing.T) {
	manifest := Manifest{}
	manifest.Spec.Runtime.Type = "command"
	manifest.Spec.Runtime.Command = &CommandSpec{
		Args: []string{"-test.run=TestCommandProcessHelper", "--", "output-error"}, ErrorPrefix: "[ERROR]",
		Artifacts: []CommandArtifact{{Name: "raw.txt", Required: true}},
	}
	result, err := CommandExecutor(manifest, os.Args[0], t.TempDir())(context.Background(), Request{Log: func(string, string) {}})
	if err == nil || !strings.Contains(err.Error(), "output reported errors") || len(result.Artifacts) != 1 || string(result.Artifacts[0].Data) != "partial evidence" || len(result.Observations) != 0 {
		t.Fatalf("zero-exit error was hidden or evidence discarded: %+v, %v", result, err)
	}
}

func TestFailureKillsPluginProcessGroup(t *testing.T) {
	for _, outcome := range []string{"cancel", "timeout", "crash"} {
		t.Run(outcome, func(t *testing.T) {
			testFailureKillsPluginProcessGroup(t, outcome)
		})
	}
}

func testFailureKillsPluginProcessGroup(t *testing.T, outcome string) {
	t.Helper()
	manifest := Manifest{}
	manifest.Metadata.ID = "OWTF-TEST-001-active"
	manifest.Spec.Techniques = []TechniqueSpec{{Code: "OWTF-TEST-001", Title: "Test", Priority: 99}}
	manifest.Spec.TargetKinds = []string{"url"}
	manifest.Spec.Runtime.Command = &CommandSpec{Args: []string{"-test.run=TestCommandProcessHelper", "--", "spawn"}}

	ctx, cancel := context.WithCancel(context.Background())
	if outcome == "timeout" {
		cancel()
		ctx, cancel = context.WithTimeout(context.Background(), 2*time.Second)
	}
	defer cancel()
	processes := make(chan int, 3)
	done := make(chan error, 1)
	wordlists := t.TempDir()
	go func() {
		_, err := CommandExecutor(manifest, os.Args[0], wordlists)(ctx, Request{
			Target: model.Target{Kind: "url", Value: "https://example.test/"},
			Log: func(stream, message string) {
				if stream == "stdout" && strings.HasPrefix(message, "process=") {
					id, _ := strconv.Atoi(strings.TrimPrefix(message, "process="))
					processes <- id
				}
			},
		})
		done <- err
	}()

	var ids []int
	defer func() {
		if len(ids) != 0 {
			_ = signalProcessGroup(ids[0], syscall.SIGKILL)
		}
	}()
	for len(ids) != 3 {
		select {
		case id := <-processes:
			if id < 2 {
				t.Fatalf("invalid helper PID %d", id)
			}
			ids = append(ids, id)
		case <-time.After(2 * time.Second):
			t.Fatal("plugin parent, child, and grandchild did not start")
		}
	}
	if outcome == "cancel" {
		cancel()
	} else if outcome == "crash" {
		if err := syscall.Kill(ids[0], syscall.SIGKILL); err != nil {
			t.Fatal(err)
		}
	}
	select {
	case err := <-done:
		var exitError *exec.ExitError
		if outcome == "cancel" && !errors.Is(err, context.Canceled) ||
			outcome == "timeout" && !errors.Is(err, context.DeadlineExceeded) ||
			outcome == "crash" && !errors.As(err, &exitError) {
			t.Fatalf("unexpected %s error: %v", outcome, err)
		}
	case <-time.After(4 * time.Second):
		t.Fatalf("plugin %s did not return", outcome)
	}
	for _, pid := range ids {
		waitForProcessExit(t, pid)
	}
	waitForProcessGroupExit(t, ids[0])
}

func TestCommandProcessHelper(t *testing.T) {
	role := os.Args[len(os.Args)-1]
	if role == "output-error" {
		if err := os.WriteFile("raw.txt", []byte("partial evidence"), 0o600); err != nil {
			t.Fatal(err)
		}
		fmt.Fprintln(os.Stderr, "[ERROR] resolver failed")
		return
	}
	if role != "spawn" && role != "child" && role != "leaf" {
		return
	}
	signal.Ignore(syscall.SIGTERM)
	fmt.Printf("process=%d\n", os.Getpid())
	if role == "leaf" {
		for {
			time.Sleep(time.Hour)
		}
	}
	next := "child"
	if role == "child" {
		next = "leaf"
	}
	child := exec.Command(os.Args[0], "-test.run=TestCommandProcessHelper", "--", next)
	child.Stdout = os.Stdout
	child.Stderr = os.Stderr
	if err := child.Start(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	_ = child.Wait()
	os.Exit(0)
}

func waitForProcessExit(t *testing.T, pid int) {
	t.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for {
		err := syscall.Kill(pid, 0)
		if err == syscall.ESRCH {
			return
		}
		if time.Now().After(deadline) {
			t.Fatalf("process %d survived cleanup", pid)
		}
		time.Sleep(20 * time.Millisecond)
	}
}

func waitForProcessGroupExit(t *testing.T, processGroupID int) {
	t.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for {
		err := syscall.Kill(-processGroupID, 0)
		if err == syscall.ESRCH {
			return
		}
		if time.Now().After(deadline) {
			t.Fatalf("process group %d survived cleanup", processGroupID)
		}
		time.Sleep(20 * time.Millisecond)
	}
}
