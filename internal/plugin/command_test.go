//go:build !windows

package plugin

import (
	"context"
	"fmt"
	"os"
	"os/exec"
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

func TestCancellationKillsPluginProcessGroup(t *testing.T) {
	manifest := Manifest{}
	manifest.Metadata.ID = "OWTF-TEST-001-active"
	manifest.Spec.Techniques = []TechniqueSpec{{Code: "OWTF-TEST-001", Title: "Test", Priority: 99}}
	manifest.Spec.TargetKinds = []string{"url"}
	manifest.Spec.Runtime.Command = &CommandSpec{Args: []string{"-test.run=TestCommandProcessHelper", "--", "spawn"}}

	ctx, cancel := context.WithCancel(context.Background())
	processes := make(chan []int, 1)
	done := make(chan error, 1)
	go func() {
		_, err := CommandExecutor(manifest, os.Args[0], t.TempDir())(ctx, Request{
			Target: model.Target{Kind: "url", Value: "https://example.test/"},
			Log: func(stream, message string) {
				if stream == "stdout" && strings.HasPrefix(message, "processes=") {
					parts := strings.Split(strings.TrimPrefix(message, "processes="), ",")
					ids := make([]int, 0, len(parts))
					for _, part := range parts {
						id, _ := strconv.Atoi(part)
						ids = append(ids, id)
					}
					processes <- ids
				}
			},
		})
		done <- err
	}()

	var ids []int
	select {
	case ids = <-processes:
	case <-time.After(2 * time.Second):
		t.Fatal("plugin process group did not start")
	}
	cancel()
	select {
	case err := <-done:
		if !strings.Contains(err.Error(), context.Canceled.Error()) {
			t.Fatalf("unexpected cancellation error: %v", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("plugin cancellation did not return")
	}
	for _, pid := range ids {
		waitForProcessExit(t, pid)
	}
	waitForProcessGroupExit(t, ids[0])
}

func TestCommandProcessHelper(t *testing.T) {
	if len(os.Args) < 2 || os.Args[len(os.Args)-1] != "spawn" {
		return
	}
	child := exec.Command("/bin/sh", "-c", "trap '' TERM; while :; do sleep 1; done")
	child.Stdout = os.Stdout
	child.Stderr = os.Stderr
	if err := child.Start(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	fmt.Printf("processes=%d,%d\n", os.Getpid(), child.Process.Pid)
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
			t.Fatalf("process %d survived cancellation", pid)
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
			t.Fatalf("process group %d survived cancellation", processGroupID)
		}
		time.Sleep(20 * time.Millisecond)
	}
}
