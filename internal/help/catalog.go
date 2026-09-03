package help

import (
	"bytes"
	"embed"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"net/url"
	"strings"

	"gopkg.in/yaml.v3"
)

const maximumFileSize = 256 << 10

//go:embed help.yaml
var defaultFiles embed.FS

// Link is one maintained external reference.
type Link struct {
	Title       string `json:"title" yaml:"title"`
	URL         string `json:"url" yaml:"url"`
	Description string `json:"description,omitempty" yaml:"description,omitempty"`
}

// Section retains the categories from OWTF's original Help page.
type Section struct {
	ID    string `json:"id" yaml:"id"`
	Title string `json:"title" yaml:"title"`
	Links []Link `json:"links" yaml:"links"`
}

// Catalog is the immutable operator-visible Help catalog.
type Catalog struct {
	Version  string    `json:"version"`
	Sections []Section `json:"sections"`
}

type manifest struct {
	APIVersion string `yaml:"apiVersion"`
	Kind       string `yaml:"kind"`
	Metadata   struct {
		Version string `yaml:"version"`
	} `yaml:"metadata"`
	Spec struct {
		Sections []Section `yaml:"sections"`
	} `yaml:"spec"`
}

// Default returns the Help catalog compiled into the OWTF binary.
func Default() *Catalog {
	catalog, err := Load(defaultFiles)
	if err != nil {
		panic(fmt.Sprintf("load embedded help catalog: %v", err))
	}
	return catalog
}

// Load reads and strictly validates help.yaml from fsys.
func Load(fsys fs.FS) (*Catalog, error) {
	data, err := fs.ReadFile(fsys, "help.yaml")
	if err != nil {
		return nil, err
	}
	if len(data) > maximumFileSize {
		return nil, fmt.Errorf("help.yaml exceeds %d bytes", maximumFileSize)
	}
	var value manifest
	decoder := yaml.NewDecoder(bytes.NewReader(data))
	decoder.KnownFields(true)
	if err := decoder.Decode(&value); err != nil {
		return nil, err
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		if err == nil {
			return nil, errors.New("help.yaml contains multiple YAML documents")
		}
		return nil, err
	}
	if err := validate(value); err != nil {
		return nil, err
	}
	return &Catalog{Version: value.Metadata.Version, Sections: cloneSections(value.Spec.Sections)}, nil
}

// Snapshot returns a deep copy safe for serialization by callers.
func (catalog *Catalog) Snapshot() Catalog {
	if catalog == nil {
		return Catalog{Sections: []Section{}}
	}
	return Catalog{Version: catalog.Version, Sections: cloneSections(catalog.Sections)}
}

func validate(value manifest) error {
	if value.APIVersion != "owtf.dev/v1alpha1" {
		return fmt.Errorf("unsupported apiVersion %q", value.APIVersion)
	}
	if value.Kind != "Help" {
		return errors.New("kind must be Help")
	}
	if strings.TrimSpace(value.Metadata.Version) == "" {
		return errors.New("metadata.version is required")
	}
	if len(value.Spec.Sections) == 0 || len(value.Spec.Sections) > 16 {
		return errors.New("spec.sections must contain between 1 and 16 sections")
	}
	sectionIDs := make(map[string]bool, len(value.Spec.Sections))
	links := make(map[string]bool)
	for _, section := range value.Spec.Sections {
		if !validID(section.ID) || strings.TrimSpace(section.Title) == "" {
			return fmt.Errorf("section %q requires a valid id and title", section.ID)
		}
		if sectionIDs[section.ID] {
			return fmt.Errorf("duplicate section id %q", section.ID)
		}
		sectionIDs[section.ID] = true
		if len(section.Links) == 0 || len(section.Links) > 32 {
			return fmt.Errorf("section %q must contain between 1 and 32 links", section.ID)
		}
		for _, link := range section.Links {
			if strings.TrimSpace(link.Title) == "" {
				return fmt.Errorf("section %q contains a link without a title", section.ID)
			}
			parsed, err := url.ParseRequestURI(link.URL)
			if err != nil || parsed.Scheme != "https" || parsed.Host == "" || parsed.User != nil {
				return fmt.Errorf("section %q link %q must use an absolute HTTPS URL", section.ID, link.Title)
			}
			if links[link.URL] {
				return fmt.Errorf("duplicate help URL %q", link.URL)
			}
			links[link.URL] = true
		}
	}
	return nil
}

func validID(value string) bool {
	if value == "" {
		return false
	}
	for _, character := range value {
		if character >= 'a' && character <= 'z' || character == '-' {
			continue
		}
		return false
	}
	return true
}

func cloneSections(sections []Section) []Section {
	cloned := make([]Section, len(sections))
	for index, section := range sections {
		cloned[index] = section
		cloned[index].Links = append([]Link(nil), section.Links...)
	}
	return cloned
}
