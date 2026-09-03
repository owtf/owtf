package profile

import (
	"strings"
	"testing"
	"testing/fstest"

	"github.com/owtf/owtf/internal/plugin"
)

func TestProfileOrdersWithoutHidingUnlistedPlugins(t *testing.T) {
	plugins, err := plugin.Load(fstest.MapFS{
		"a/plugin.yaml": {Data: []byte(pluginManifest("OWTF-TEST-001-active"))},
		"b/plugin.yaml": {Data: []byte(pluginManifest("OWTF-TEST-002-active"))},
		"c/plugin.yaml": {Data: []byte(pluginManifest("OWTF-TEST-003-active"))},
	})
	if err != nil {
		t.Fatal(err)
	}
	profiles, err := Load(fstest.MapFS{"default.yaml": {Data: []byte(`
apiVersion: owtf.dev/v1alpha1
kind: Profile
metadata:
  name: default
spec:
  plugins:
    - OWTF-TEST-002-active
    - OWTF-TEST-001-active
`)}})
	if err != nil {
		t.Fatal(err)
	}
	if err := profiles.ValidatePlugins(plugins); err != nil {
		t.Fatal(err)
	}
	ordered, err := profiles.Order("default", plugins.Entries())
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"OWTF-TEST-002-active", "OWTF-TEST-001-active", "OWTF-TEST-003-active"}
	for index, entry := range ordered {
		if entry.Manifest.Metadata.ID != want[index] {
			t.Fatalf("order[%d] = %q, want %q", index, entry.Manifest.Metadata.ID, want[index])
		}
	}
}

func TestProfileValidationIsStrict(t *testing.T) {
	tests := []struct {
		name string
		data string
		want string
	}{
		{"unknown field", "apiVersion: owtf.dev/v1alpha1\nkind: Profile\nmetadata: {name: default}\nspec: {plugins: [one], extra: true}\n", "field extra"},
		{"duplicate plugin", "apiVersion: owtf.dev/v1alpha1\nkind: Profile\nmetadata: {name: default}\nspec: {plugins: [one, one]}\n", "duplicate ID"},
		{"invalid name", "apiVersion: owtf.dev/v1alpha1\nkind: Profile\nmetadata: {name: Default}\nspec: {plugins: [one]}\n", "metadata.name"},
		{"multiple documents", "apiVersion: owtf.dev/v1alpha1\nkind: Profile\nmetadata: {name: default}\nspec: {plugins: [one]}\n---\n{}\n", "multiple YAML documents"},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			_, err := Load(fstest.MapFS{"test.yaml": {Data: []byte(test.data)}})
			if err == nil || !strings.Contains(err.Error(), test.want) {
				t.Fatalf("Load() error = %v, want %q", err, test.want)
			}
		})
	}
}

func TestProfileRejectsUnknownPlugin(t *testing.T) {
	plugins, err := plugin.Load(fstest.MapFS{})
	if err != nil {
		t.Fatal(err)
	}
	profiles, err := Load(fstest.MapFS{"default.yaml": {Data: []byte(`
apiVersion: owtf.dev/v1alpha1
kind: Profile
metadata: {name: default}
spec: {plugins: [OWTF-MISSING-001-active]}
`)}})
	if err != nil {
		t.Fatal(err)
	}
	if err := profiles.ValidatePlugins(plugins); err == nil || !strings.Contains(err.Error(), "unknown plugin") {
		t.Fatalf("ValidatePlugins() error = %v", err)
	}
	if _, err := profiles.Order("missing", nil); err == nil {
		t.Fatal("unknown profile was accepted")
	}
}

func pluginManifest(id string) string {
	code, _, _ := strings.Cut(id, "-active")
	return `apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: ` + id + `
  version: 0.1.0
  title: Test
spec:
  techniques: [` + code + `]
  group: web
  type: active
  targetKinds: [url]
  runtime:
    type: builtin
    builtin: test
`
}
