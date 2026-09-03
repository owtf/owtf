package plugin

import (
	"encoding/csv"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
)

func TestPluginLayoutMatchesManifest(t *testing.T) {
	const root = "../../plugins"
	groups := map[string]bool{"web": true, "network": true, "auxiliary": true, "community": true}
	manifests := 0
	err := filepath.WalkDir(root, func(filePath string, entry os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if entry.IsDir() || entry.Name() != "plugin.yaml" {
			return nil
		}
		relative, err := filepath.Rel(root, filePath)
		if err != nil {
			return err
		}
		parts := strings.Split(filepath.ToSlash(relative), "/")
		if len(parts) != 4 || !groups[parts[0]] {
			t.Fatalf("plugin manifest %q must use <group>/<code>/<type>/plugin.yaml", relative)
		}
		catalog, err := Load(os.DirFS(filepath.Dir(filePath)))
		if err != nil {
			t.Fatalf("load %s: %v", relative, err)
		}
		if len(catalog.entries) != 1 {
			t.Fatalf("plugin directory %q produced %d catalog entries", relative, len(catalog.entries))
		}
		for _, plugin := range catalog.entries {
			expectedID := parts[1] + "-" + parts[2]
			if plugin.Manifest.Spec.Group != parts[0] || plugin.Manifest.Spec.Type != parts[2] || plugin.Manifest.Metadata.ID != expectedID {
				t.Fatalf("plugin %q does not match path %q", plugin.Manifest.Metadata.ID, relative)
			}
		}
		manifests++
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if manifests == 0 {
		t.Fatal("plugin tree has no manifests")
	}
}

func TestEveryLegacyPluginHasAReviewedDecision(t *testing.T) {
	inventory := readCSV(t, "../../docs/architecture/legacy-plugin-inventory.csv", 8)
	decisions := readCSV(t, "../../docs/architecture/plugin-support-decisions.csv", 8)
	catalog, err := Load(os.DirFS("../../plugins"))
	if err != nil {
		t.Fatal(err)
	}

	remaining := make(map[string]bool, len(inventory))
	for _, row := range inventory {
		key := decisionKey(row)
		if remaining[key] {
			t.Fatalf("duplicate legacy inventory row %s", key)
		}
		remaining[key] = true
	}
	seen := make(map[string]bool, len(decisions))
	for _, row := range decisions {
		key := decisionKey(row)
		if seen[key] {
			t.Fatalf("duplicate plugin decision %s", key)
		}
		seen[key] = true
		if !remaining[key] {
			t.Fatalf("plugin decision %s has no legacy inventory row", key)
		}
		delete(remaining, key)
		decision, replacement, status, rationale := row[4], row[5], row[6], row[7]
		if strings.TrimSpace(rationale) == "" {
			t.Fatalf("plugin decision %s has no rationale", key)
		}
		switch decision {
		case "replace":
			if replacement == "" || status != "implemented" && status != "planned" {
				t.Fatalf("replacement decision %s has invalid replacement or status", key)
			}
			if _, ok := catalog.Get(replacement); !ok {
				t.Fatalf("replacement %q for %s is not in the plugin catalog", replacement, key)
			}
		case "reject", "defer":
			if replacement != "" || status != "reviewed" {
				t.Fatalf("%s decision %s must be reviewed without a replacement", decision, key)
			}
		default:
			t.Fatalf("plugin decision %s uses unsupported decision %q", key, decision)
		}
	}
	if len(remaining) != 0 {
		missing := make([]string, 0, len(remaining))
		for key := range remaining {
			missing = append(missing, key)
		}
		sort.Strings(missing)
		t.Fatalf("%d legacy plugin variants lack a decision, including %s", len(missing), missing[0])
	}
}

func readCSV(t *testing.T, path string, fields int) [][]string {
	t.Helper()
	file, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	reader := csv.NewReader(file)
	header, err := reader.Read()
	if err != nil || len(header) != fields {
		t.Fatalf("read %s header: fields=%d err=%v", path, len(header), err)
	}
	var rows [][]string
	for {
		row, err := reader.Read()
		if err == io.EOF {
			return rows
		}
		if err != nil || len(row) != fields {
			t.Fatalf("read %s: fields=%d err=%v", path, len(row), err)
		}
		rows = append(rows, row)
	}
}

func decisionKey(row []string) string {
	return strings.Join(row[:3], "/")
}
