// Command check-settings-audit verifies inventory coverage against pinned legacy
// Git blobs without importing or executing the retired Python application.
package main

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
)

type source struct {
	Commit string `json:"commit"`
	Files  []struct {
		Path    string `json:"path"`
		SHA256  string `json:"sha256"`
		Entries int    `json:"entries"`
	} `json:"files"`
}

func main() {
	if err := check(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func check() error {
	data, err := os.ReadFile("docs/architecture/settings-migration-source.json")
	if err != nil {
		return err
	}
	var manifest source
	if err := json.Unmarshal(data, &manifest); err != nil {
		return err
	}
	file, err := os.Open("docs/architecture/settings-migration.csv")
	if err != nil {
		return err
	}
	defer file.Close()
	rows, err := csv.NewReader(file).ReadAll()
	if err != nil {
		return err
	}
	if len(rows) == 0 || strings.Join(rows[0], ",") != "source,line,key,line_sha256,status,replacement,evidence,decision" {
		return fmt.Errorf("unexpected audit columns")
	}
	inventory := make(map[string][]string)
	for _, row := range rows[1:] {
		id := row[0] + ":" + row[1]
		if _, exists := inventory[id]; exists {
			return fmt.Errorf("duplicate occurrence %s", id)
		}
		switch row[4] {
		case "migrated", "replaced", "partial", "removed", "deferred", "gap":
		default:
			return fmt.Errorf("invalid status at %s", id)
		}
		for _, value := range row {
			if strings.TrimSpace(value) == "" {
				return fmt.Errorf("empty audit field at %s", id)
			}
		}
		for _, path := range strings.Split(row[6], "; ") {
			if _, err := os.Stat(path); err != nil {
				return fmt.Errorf("%s evidence: %w", id, err)
			}
		}
		inventory[id] = row
	}
	settings := regexp.MustCompile(`^\s*([A-Z][A-Z_0-9]*)\s*=`)
	yamlKey := regexp.MustCompile(`^\s*- config:\s*(\S+)`)
	total := 0
	for _, sourceFile := range manifest.Files {
		blob, err := exec.Command("git", "show", manifest.Commit+":"+sourceFile.Path).Output()
		if err != nil {
			return fmt.Errorf("read pinned source %s (fetch commit %s if absent): %w", sourceFile.Path, manifest.Commit, err)
		}
		if fmt.Sprintf("%x", sha256.Sum256(blob)) != sourceFile.SHA256 {
			return fmt.Errorf("source hash mismatch: %s", sourceFile.Path)
		}
		count := 0
		for index, line := range strings.Split(string(blob), "\n") {
			key := ""
			switch {
			case strings.HasSuffix(sourceFile.Path, ".py"):
				if match := settings.FindStringSubmatch(line); match != nil {
					key = match[1]
				}
			case strings.HasSuffix(sourceFile.Path, ".yaml"):
				if match := yamlKey.FindStringSubmatch(line); match != nil {
					key = match[1]
				}
			case strings.HasSuffix(sourceFile.Path, ".cfg"):
				trimmed := strings.TrimSpace(line)
				if trimmed != "" && !strings.HasPrefix(trimmed, "#") {
					key = strings.TrimSpace(strings.SplitN(line, "_____", 2)[0])
				}
			}
			if key == "" {
				continue
			}
			id := sourceFile.Path + ":" + strconv.Itoa(index+1)
			row, ok := inventory[id]
			if !ok || row[2] != key || row[3] != fmt.Sprintf("%x", sha256.Sum256([]byte(line))) {
				return fmt.Errorf("missing or mismatched audit occurrence: %s (%s)", id, key)
			}
			delete(inventory, id)
			count++
		}
		if count != sourceFile.Entries {
			return fmt.Errorf("entry count mismatch: %s", sourceFile.Path)
		}
		total += count
	}
	if len(inventory) != 0 {
		return fmt.Errorf("%d audit rows have no source occurrence", len(inventory))
	}
	fmt.Printf("PASS: %d settings/resource occurrences match pinned source; evidence paths exist.\n", total)
	return nil
}
