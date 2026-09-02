package plugin

import (
	"testing"
	"testing/fstest"
)

func TestCommandManifestRejectsShellAndPartialInterpolation(t *testing.T) {
	for name, runtime := range map[string]string{
		"shell":   "executable: sh\n      args: []",
		"partial": "executable: curl\n      args: ['--url={{target}}']",
	} {
		t.Run(name, func(t *testing.T) {
			_, err := Load(fstest.MapFS{"plugin.yaml": &fstest.MapFile{Data: []byte(commandManifest(runtime, ""))}})
			if err == nil {
				t.Fatal("unsafe command manifest was accepted")
			}
		})
	}
}

func TestMissingRequirementIsVisible(t *testing.T) {
	executable := "command-that-does-not-exist-owtf"
	catalog, err := Load(fstest.MapFS{"plugin.yaml": &fstest.MapFile{Data: []byte(commandManifest("executable: "+executable, executable))}})
	if err != nil {
		t.Fatal(err)
	}
	catalog.ResolveCommands()
	entry, _ := catalog.Get("OWTF-TEST-001-active")
	if entry.Availability != "missing_requirements" || entry.Reason == "" || entry.Executor != nil {
		t.Fatalf("missing command was not surfaced: %+v", entry)
	}
}

func commandManifest(runtime, requirement string) string {
	requirements := ""
	if requirement != "" {
		requirements = "  requirements:\n    commands: [" + requirement + "]\n"
	}
	return `apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-TEST-001-active
  version: 0.1.0
  title: Command test
spec:
  techniques: [OWTF-TEST-001]
  variant: active
` + requirements + `  runtime:
    type: command
    command:
      ` + runtime + "\n"
}
