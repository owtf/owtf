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

func TestTechniqueMetadataIsExposedAndConsistent(t *testing.T) {
	manifest := strings.Replace(commandManifest("executable: echo", ""),
		"  techniques: [OWTF-TEST-001]", `  techniques:
    - code: OWTF-TEST-001
      title: Test technique
      hint: Inspect the response.
      priority: 10
      reference: https://example.test/reference`, 1)
	catalog, err := Load(fstest.MapFS{"active/plugin.yaml": {Data: []byte(manifest)}})
	if err != nil {
		t.Fatal(err)
	}
	entry, _ := catalog.Get("OWTF-TEST-001-active")
	technique := entry.Plugin().Techniques[0]
	if technique.Code != "OWTF-TEST-001" || technique.Title != "Test technique" ||
		technique.Hint != "Inspect the response." || technique.Priority != 10 ||
		technique.Reference != "https://example.test/reference" {
		t.Fatalf("unexpected technique metadata: %+v", technique)
	}

	for name, invalid := range map[string]string{
		"wrong ID":          strings.Replace(manifest, "id: OWTF-TEST-001-active", "id: OWTF-OTHER-001-active", 1),
		"negative priority": strings.Replace(manifest, "priority: 10", "priority: -1", 1),
		"invalid reference": strings.Replace(manifest, "https://example.test/reference", "file:///tmp/reference", 1),
		"unknown field":     strings.Replace(manifest, "      hint:", "      category: web\n      hint:", 1),
		"multiple codes":    strings.Replace(manifest, "  group: web", "    - OWTF-TEST-002\n  group: web", 1),
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(invalid)}}); err == nil {
				t.Fatal("invalid technique metadata was accepted")
			}
		})
	}

	passive := strings.Replace(manifest, "id: OWTF-TEST-001-active", "id: OWTF-TEST-001-passive", 1)
	passive = strings.Replace(passive, "type: active", "type: passive", 1)
	passive = strings.Replace(passive, "hint: Inspect the response.", "hint: Different metadata.", 1)
	if _, err := Load(fstest.MapFS{
		"active/plugin.yaml":  {Data: []byte(manifest)},
		"passive/plugin.yaml": {Data: []byte(passive)},
	}); err == nil {
		t.Fatal("conflicting metadata for one OWTF code was accepted")
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
