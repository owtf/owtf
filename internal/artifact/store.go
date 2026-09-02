package artifact

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// Stored identifies content written to the artifact store.
type Stored struct {
	SHA256 string
	Path   string
	Size   int64
}

// Store persists content-addressed artifacts below one configured root.
type Store struct {
	root string
}

// New creates an artifact store rooted at root.
func New(root string) (*Store, error) {
	if err := os.MkdirAll(root, 0o750); err != nil {
		return nil, fmt.Errorf("create artifact store: %w", err)
	}
	return &Store{root: root}, nil
}

// Put atomically stores data and returns its digest, relative path, and size.
func (s *Store) Put(data []byte) (Stored, error) {
	sum := sha256.Sum256(data)
	digest := hex.EncodeToString(sum[:])
	relative := filepath.Join(digest[:2], digest)
	path := filepath.Join(s.root, relative)
	if info, err := os.Stat(path); err == nil {
		return Stored{SHA256: digest, Path: relative, Size: info.Size()}, nil
	} else if !os.IsNotExist(err) {
		return Stored{}, fmt.Errorf("inspect artifact: %w", err)
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o750); err != nil {
		return Stored{}, fmt.Errorf("create artifact directory: %w", err)
	}
	tmp, err := os.CreateTemp(filepath.Dir(path), ".artifact-*")
	if err != nil {
		return Stored{}, fmt.Errorf("create artifact temp file: %w", err)
	}
	tmpName := tmp.Name()
	defer os.Remove(tmpName)
	if err := tmp.Chmod(0o640); err != nil {
		tmp.Close()
		return Stored{}, fmt.Errorf("set artifact permissions: %w", err)
	}
	if _, err := tmp.Write(data); err != nil {
		tmp.Close()
		return Stored{}, fmt.Errorf("write artifact: %w", err)
	}
	if err := tmp.Close(); err != nil {
		return Stored{}, fmt.Errorf("close artifact: %w", err)
	}
	if err := os.Rename(tmpName, path); err != nil {
		if _, statErr := os.Stat(path); statErr != nil {
			return Stored{}, fmt.Errorf("publish artifact: %w", err)
		}
	}
	return Stored{SHA256: digest, Path: relative, Size: int64(len(data))}, nil
}

// Open returns a retained artifact after verifying that relative cannot escape
// the store root.
func (s *Store) Open(relative string) (*os.File, error) {
	clean := filepath.Clean(relative)
	if clean == "." || filepath.IsAbs(clean) || clean == ".." || strings.HasPrefix(clean, ".."+string(filepath.Separator)) {
		return nil, fmt.Errorf("invalid artifact path")
	}
	return os.Open(filepath.Join(s.root, clean))
}
