package plugin

import (
	"strings"
	"testing"
	"testing/fstest"
)

func TestManifestUsesOWTFPluginGroupAndType(t *testing.T) {
	valid := commandManifest("executable: echo", "")
	for name, manifest := range map[string]string{
		"missing group": strings.Replace(valid, "  group: web\n", "", 1),
		"unknown group": strings.Replace(valid, "  group: web", "  group: cloud", 1),
		"missing type":  strings.Replace(valid, "  type: active\n", "", 1),
		"unknown type":  strings.Replace(valid, "  type: active", "  type: automatic", 1),
		"old variant":   strings.Replace(valid, "  type: active", "  variant: active", 1),
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := Load(fstest.MapFS{"plugin.yaml": &fstest.MapFile{Data: []byte(manifest)}}); err == nil {
				t.Fatal("invalid plugin group/type was accepted")
			}
		})
	}
}

func TestEntriesByGroupType(t *testing.T) {
	active := commandManifest("executable: echo", "")
	passive := strings.ReplaceAll(active, "OWTF-TEST-001-active", "OWTF-TEST-002-passive")
	passive = strings.ReplaceAll(passive, "OWTF-TEST-001", "OWTF-TEST-002")
	passive = strings.Replace(passive, "type: active", "type: passive", 1)
	catalog, err := Load(fstest.MapFS{
		"active/plugin.yaml":  &fstest.MapFile{Data: []byte(active)},
		"passive/plugin.yaml": &fstest.MapFile{Data: []byte(passive)},
	})
	if err != nil {
		t.Fatal(err)
	}
	entries := catalog.EntriesByGroupType("web", []string{"passive"})
	if len(entries) != 1 || entries[0].Manifest.Metadata.ID != "OWTF-TEST-002-passive" {
		t.Fatalf("unexpected group/type selection: %+v", entries)
	}
}

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
  group: web
  type: active
` + requirements + `  runtime:
    type: command
    command:
      ` + runtime + "\n"
}
