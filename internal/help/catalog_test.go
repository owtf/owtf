package help

import (
	"strings"
	"testing"
	"testing/fstest"
)

func TestDefaultCatalogRetainsOWTFHelpSections(t *testing.T) {
	catalog := Default().Snapshot()
	want := []string{"exploitation", "methodology", "calculators", "test-learn", "owtf-help-links"}
	if catalog.Version == "" || len(catalog.Sections) != len(want) {
		t.Fatalf("unexpected help catalog: %+v", catalog)
	}
	for index, id := range want {
		if catalog.Sections[index].ID != id || len(catalog.Sections[index].Links) == 0 {
			t.Fatalf("section %d = %+v, want %q with links", index, catalog.Sections[index], id)
		}
	}
}

func TestLoadRejectsUnknownFieldsAndUnsafeURLs(t *testing.T) {
	base := `apiVersion: owtf.dev/v1alpha1
kind: Help
metadata:
  version: "1"
spec:
  sections:
    - id: methodology
      title: Methodology
      links:
        - title: OWASP
          url: https://owasp.org/
`
	for name, data := range map[string]string{
		"unknown field": base + "unexpected: true\n",
		"insecure URL":  strings.Replace(base, "https://owasp.org/", "http://owasp.org/", 1),
	} {
		t.Run(name, func(t *testing.T) {
			_, err := Load(fstest.MapFS{"help.yaml": {Data: []byte(data)}})
			if err == nil {
				t.Fatal("invalid help catalog was accepted")
			}
		})
	}
}

func TestSnapshotDoesNotExposeCatalogState(t *testing.T) {
	catalog := Default()
	snapshot := catalog.Snapshot()
	snapshot.Sections[0].Links[0].Title = "changed"
	if catalog.Snapshot().Sections[0].Links[0].Title == "changed" {
		t.Fatal("snapshot mutated the catalog")
	}
}
