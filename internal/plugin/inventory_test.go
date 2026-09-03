package plugin

import (
	"encoding/csv"
	"io"
	"os"
	"sort"
	"strings"
	"testing"
)

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
			if status == "implemented" {
				if _, ok := catalog.Get(replacement); !ok {
					t.Fatalf("implemented replacement %q for %s is not in the plugin catalog", replacement, key)
				}
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
