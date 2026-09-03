package profile

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"path"
	"sort"
	"strings"

	"github.com/owtf/owtf/internal/plugin"
	"gopkg.in/yaml.v3"
)

const maximumFileSize = 1 << 20

// Manifest is the strict on-disk representation of one plugin order profile.
type Manifest struct {
	APIVersion string `json:"apiVersion" yaml:"apiVersion"`
	Kind       string `json:"kind" yaml:"kind"`
	Metadata   struct {
		Name        string `json:"name" yaml:"name"`
		Description string `json:"description,omitempty" yaml:"description,omitempty"`
	} `json:"metadata" yaml:"metadata"`
	Spec struct {
		Plugins []string `json:"plugins" yaml:"plugins"`
	} `json:"spec" yaml:"spec"`
}

// Profile is the operator-visible form of a plugin order profile.
type Profile struct {
	Name        string   `json:"name"`
	Description string   `json:"description,omitempty"`
	Plugins     []string `json:"plugins"`
}

// Catalog is an immutable set of named profiles.
type Catalog struct {
	profiles map[string]Profile
}

// Empty returns a profile catalog with no configured ordering.
func Empty() *Catalog {
	return &Catalog{profiles: make(map[string]Profile)}
}

// Load recursively reads YAML profiles from fsys. Loading fails as a unit so
// an invalid profile cannot silently change execution order.
func Load(fsys fs.FS) (*Catalog, error) {
	catalog := Empty()
	err := fs.WalkDir(fsys, ".", func(filePath string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if entry.IsDir() || (path.Ext(entry.Name()) != ".yaml" && path.Ext(entry.Name()) != ".yml") {
			return nil
		}
		data, err := fs.ReadFile(fsys, filePath)
		if err != nil {
			return err
		}
		if len(data) > maximumFileSize {
			return fmt.Errorf("profile %s exceeds %d bytes", filePath, maximumFileSize)
		}
		manifest, err := decode(data)
		if err != nil {
			return fmt.Errorf("parse %s: %w", filePath, err)
		}
		if err := validate(manifest); err != nil {
			return fmt.Errorf("validate %s: %w", filePath, err)
		}
		name := manifest.Metadata.Name
		if _, exists := catalog.profiles[name]; exists {
			return fmt.Errorf("duplicate profile %q", name)
		}
		catalog.profiles[name] = Profile{
			Name: name, Description: manifest.Metadata.Description,
			Plugins: append([]string(nil), manifest.Spec.Plugins...),
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	return catalog, nil
}

// ValidatePlugins rejects profile entries that do not exist in the plugin
// catalog. A misspelled ID must not silently alter task order.
func (catalog *Catalog) ValidatePlugins(plugins *plugin.Catalog) error {
	if catalog == nil || plugins == nil {
		return errors.New("profile and plugin catalogs are required")
	}
	for _, profile := range catalog.List() {
		for _, id := range profile.Plugins {
			if _, ok := plugins.Get(id); !ok {
				return fmt.Errorf("profile %q references unknown plugin %q", profile.Name, id)
			}
		}
	}
	return nil
}

// List returns profiles sorted by name.
func (catalog *Catalog) List() []Profile {
	if catalog == nil {
		return []Profile{}
	}
	result := make([]Profile, 0, len(catalog.profiles))
	for _, profile := range catalog.profiles {
		profile.Plugins = append([]string(nil), profile.Plugins...)
		result = append(result, profile)
	}
	sort.Slice(result, func(i, j int) bool { return result[i].Name < result[j].Name })
	return result
}

// Get returns one profile by name.
func (catalog *Catalog) Get(name string) (Profile, bool) {
	if catalog == nil {
		return Profile{}, false
	}
	profile, ok := catalog.profiles[name]
	profile.Plugins = append([]string(nil), profile.Plugins...)
	return profile, ok
}

// Order applies a profile to entries without excluding unlisted plugins.
// Unlisted entries follow listed entries in stable plugin-ID order.
func (catalog *Catalog) Order(name string, entries []plugin.Entry) ([]plugin.Entry, error) {
	profile, ok := catalog.Get(name)
	if !ok {
		return nil, fmt.Errorf("profile %q does not exist", name)
	}
	positions := make(map[string]int, len(profile.Plugins))
	for index, id := range profile.Plugins {
		positions[id] = index
	}
	ordered := append([]plugin.Entry(nil), entries...)
	sort.SliceStable(ordered, func(i, j int) bool {
		left := ordered[i].Manifest.Metadata.ID
		right := ordered[j].Manifest.Metadata.ID
		leftPosition, leftListed := positions[left]
		rightPosition, rightListed := positions[right]
		switch {
		case leftListed && rightListed:
			return leftPosition < rightPosition
		case leftListed:
			return true
		case rightListed:
			return false
		default:
			return left < right
		}
	})
	return ordered, nil
}

func decode(data []byte) (Manifest, error) {
	var manifest Manifest
	decoder := yaml.NewDecoder(bytes.NewReader(data))
	decoder.KnownFields(true)
	if err := decoder.Decode(&manifest); err != nil {
		return Manifest{}, err
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		if err == nil {
			return Manifest{}, errors.New("profile contains multiple YAML documents")
		}
		return Manifest{}, err
	}
	return manifest, nil
}

func validate(manifest Manifest) error {
	if manifest.APIVersion != "owtf.dev/v1alpha1" {
		return fmt.Errorf("unsupported apiVersion %q", manifest.APIVersion)
	}
	if manifest.Kind != "Profile" {
		return errors.New("kind must be Profile")
	}
	if !validName(manifest.Metadata.Name) {
		return errors.New("metadata.name must use lowercase letters, digits, hyphens, or underscores")
	}
	if len(manifest.Spec.Plugins) == 0 {
		return errors.New("spec.plugins cannot be empty")
	}
	seen := make(map[string]bool, len(manifest.Spec.Plugins))
	for _, id := range manifest.Spec.Plugins {
		if strings.TrimSpace(id) == "" {
			return errors.New("spec.plugins contains an empty ID")
		}
		if seen[id] {
			return fmt.Errorf("spec.plugins contains duplicate ID %q", id)
		}
		seen[id] = true
	}
	return nil
}

func validName(value string) bool {
	if value == "" {
		return false
	}
	for _, character := range value {
		if character >= 'a' && character <= 'z' || character >= '0' && character <= '9' || character == '-' || character == '_' {
			continue
		}
		return false
	}
	return true
}
