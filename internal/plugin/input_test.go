package plugin

import (
	"encoding/json"
	"strings"
	"testing"
	"testing/fstest"
)

func TestPluginInputsResolveAndSnapshot(t *testing.T) {
	catalog, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(inputManifest)}})
	if err != nil {
		t.Fatal(err)
	}
	entry, _ := catalog.Get("OWTF-TEST-001-active")
	resolved, err := entry.ResolveInputs(map[string]any{
		"user_agent":      "OWTF; $(touch /tmp/not-run)",
		"timeout_seconds": "7",
	})
	if err != nil {
		t.Fatal(err)
	}
	if resolved["timeout_seconds"] != int64(7) || resolved["follow_redirects"] != true || resolved["mode"] != "safe" {
		t.Fatalf("unexpected resolved inputs: %#v", resolved)
	}
	snapshotJSON, err := entry.Snapshot(map[string]any{"user_agent": "OWTF", "mode": "fast"})
	if err != nil {
		t.Fatal(err)
	}
	snapshot, err := ParseSnapshot(snapshotJSON)
	if err != nil {
		t.Fatal(err)
	}
	if !snapshot.Matches(entry.Manifest) || snapshot.Inputs["timeout_seconds"] != int64(20) || snapshot.Inputs["mode"] != "fast" {
		t.Fatalf("unexpected task snapshot: %+v", snapshot)
	}
	codeOnly := strings.Replace(snapshotJSON,
		`"techniques":[{"code":"OWTF-TEST-001","title":"Input test","priority":99}]`,
		`"techniques":["OWTF-TEST-001"]`, 1)
	if codeOnly == snapshotJSON {
		t.Fatal("test snapshot did not contain structured technique metadata")
	}
	oldSnapshot, err := ParseSnapshot(codeOnly)
	if err != nil || oldSnapshot.Manifest.Spec.Techniques[0].Title != "Input test" ||
		oldSnapshot.Manifest.Spec.Techniques[0].Priority != 99 {
		t.Fatalf("code-only task snapshot was not migrated: snapshot=%+v err=%v", oldSnapshot, err)
	}
	changed := entry.Manifest
	changed.Metadata.Version = "0.2.0"
	if snapshot.Matches(changed) {
		t.Fatal("changed manifest matched the task snapshot")
	}

	legacy, _ := json.Marshal(entry.Manifest)
	legacySnapshot, err := ParseSnapshot(string(legacy))
	if err != nil || legacySnapshot.Version != 0 || len(legacySnapshot.Inputs) != 0 {
		t.Fatalf("legacy snapshot was not accepted: snapshot=%+v err=%v", legacySnapshot, err)
	}
}

func TestPluginInputsRejectInvalidSchemasAndValues(t *testing.T) {
	for name, replacement := range map[string]string{
		"invalid name":           "name: Bad-Name",
		"invalid type":           "type: number",
		"invalid default":        "default: wrong",
		"choices on integer":     "choices: [one]",
		"undeclared placeholder": "{{input:missing}}",
		"partial placeholder":    "prefix-{{input:user_agent}}",
	} {
		t.Run(name, func(t *testing.T) {
			manifest := inputManifest
			switch name {
			case "invalid name":
				manifest = strings.Replace(manifest, "name: user_agent", replacement, 1)
			case "invalid type":
				manifest = strings.Replace(manifest, "type: string", replacement, 1)
			case "invalid default":
				manifest = strings.Replace(manifest, "default: 20", replacement, 1)
			case "choices on integer":
				manifest = strings.Replace(manifest, "default: 20", "default: 20\n      "+replacement, 1)
			case "undeclared placeholder", "partial placeholder":
				manifest = strings.Replace(manifest, "{{input:user_agent}}", replacement, 1)
			}
			if _, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(manifest)}}); err == nil {
				t.Fatal("invalid input contract was accepted")
			}
		})
	}

	catalog, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(inputManifest)}})
	if err != nil {
		t.Fatal(err)
	}
	entry, _ := catalog.Get("OWTF-TEST-001-active")
	for name, inputs := range map[string]map[string]any{
		"missing required":      {},
		"unknown":               {"user_agent": "OWTF", "extra": true},
		"wrong boolean":         {"user_agent": "OWTF", "follow_redirects": "yes"},
		"wrong integer":         {"user_agent": "OWTF", "timeout_seconds": 1.5},
		"integer above maximum": {"user_agent": "OWTF", "timeout_seconds": 301},
		"unknown choice":        {"user_agent": "OWTF", "mode": "reckless"},
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := entry.ResolveInputs(inputs); err == nil {
				t.Fatal("invalid input values were accepted")
			}
		})
	}
}

const inputManifest = `apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-TEST-001-active
  version: 0.1.0
  title: Input test
spec:
  techniques: [OWTF-TEST-001]
  group: web
  type: active
  inputs:
    - name: user_agent
      type: string
      required: true
    - name: timeout_seconds
      type: integer
      default: 20
      minimum: 1
      maximum: 300
    - name: follow_redirects
      type: boolean
      default: true
    - name: mode
      type: string
      choices: [fast, safe]
      default: safe
  runtime:
    type: command
    command:
      executable: curl
      args: [--user-agent, "{{input:user_agent}}", --max-time, "{{input:timeout_seconds}}", "{{target}}"]
`
