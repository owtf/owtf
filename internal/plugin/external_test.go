package plugin

import (
	"context"
	"encoding/json"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/owtf/owtf/internal/model"
)

func TestExternalExecutorReturnsGuidanceWithoutTraffic(t *testing.T) {
	catalog, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(externalManifest())}})
	if err != nil {
		t.Fatal(err)
	}
	entry, ok := catalog.Get("OWTF-TEST-001-external")
	if !ok || entry.Availability != "ready" || entry.Executor == nil {
		t.Fatalf("external plugin is not ready: %+v", entry)
	}

	var logs []string
	result, err := entry.Executor(context.Background(), Request{
		Target: model.Target{Kind: "url", Value: "http://127.0.0.1:1/must-not-be-requested"},
		Log: func(_, message string) {
			logs = append(logs, message)
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Transactions) != 0 || len(result.Artifacts) != 0 || len(result.Findings) != 0 || len(result.Observations) != 1 {
		t.Fatalf("unexpected external result: %+v", result)
	}
	observation := result.Observations[0]
	if observation.TechniqueCode != "OWTF-TEST-001" || observation.Kind != model.ObservationKindExternalReferences {
		t.Fatalf("unexpected observation: %+v", observation)
	}
	var output model.ExternalOutput
	if err := json.Unmarshal([]byte(observation.Data), &output); err != nil {
		t.Fatal(err)
	}
	if output.Guidance != "Review the target manually." || len(output.References) != 1 ||
		output.References[0].URL != "https://example.test/guide" || len(logs) != 1 {
		t.Fatalf("unexpected external output: output=%+v logs=%v", output, logs)
	}
}

func TestExternalManifestValidation(t *testing.T) {
	valid := externalManifest()
	for name, manifest := range map[string]string{
		"missing guidance":    strings.Replace(valid, "      guidance: Review the target manually.\n", "", 1),
		"missing references":  strings.Replace(valid, "      references:\n        - title: Testing guide\n          url: https://example.test/guide\n", "", 1),
		"unsafe URL":          strings.Replace(valid, "https://example.test/guide", "file:///tmp/guide", 1),
		"credential URL":      strings.Replace(valid, "https://example.test/guide", "https://user:secret@example.test/guide", 1),
		"duplicate URL":       strings.Replace(valid, "      references:\n", "      references:\n        - title: Duplicate\n          url: https://example.test/guide\n", 1),
		"mixed runtime":       strings.Replace(valid, "      guidance:", "      executable: echo\n      guidance:", 1),
		"command requirement": strings.Replace(valid, "  runtime:\n", "  requirements:\n    commands: [curl]\n  runtime:\n", 1),
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(manifest)}}); err == nil {
				t.Fatal("invalid external manifest was accepted")
			}
		})
	}
}

func externalManifest() string {
	return `apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-TEST-001-external
  version: 0.1.0
  title: External test
spec:
  techniques: [OWTF-TEST-001]
  group: web
  type: external
  targetKinds: [url]
  runtime:
    type: external
    external:
      guidance: Review the target manually.
      references:
        - title: Testing guide
          url: https://example.test/guide
`
}
