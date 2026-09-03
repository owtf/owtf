package proxy

import (
	"crypto/x509"
	"encoding/pem"
	"os"
	"path/filepath"
	"testing"
)

func TestLoadOrCreateAuthorityPersistsStableCA(t *testing.T) {
	directory := t.TempDir()
	certificatePath := filepath.Join(directory, "ca.crt")
	keyPath := filepath.Join(directory, "ca.key")
	first, err := LoadOrCreateAuthority(certificatePath, keyPath)
	if err != nil {
		t.Fatal(err)
	}
	second, err := LoadOrCreateAuthority(certificatePath, keyPath)
	if err != nil {
		t.Fatal(err)
	}
	if string(first.CertificatePEM()) != string(second.CertificatePEM()) {
		t.Fatal("proxy CA changed when reloaded")
	}
	block, _ := pem.Decode(first.CertificatePEM())
	if block == nil {
		t.Fatal("proxy CA is not PEM encoded")
	}
	certificate, err := x509.ParseCertificate(block.Bytes)
	if err != nil {
		t.Fatal(err)
	}
	if !certificate.IsCA || certificate.Subject.CommonName != "OWTF Proxy CA" {
		t.Fatalf("unexpected proxy CA: %+v", certificate.Subject)
	}
	info, err := os.Stat(keyPath)
	if err != nil {
		t.Fatal(err)
	}
	if info.Mode().Perm() != 0o600 {
		t.Fatalf("proxy CA key permissions = %o, want 600", info.Mode().Perm())
	}
}

func TestLoadOrCreateAuthorityRejectsPartialPair(t *testing.T) {
	directory := t.TempDir()
	if err := os.WriteFile(filepath.Join(directory, "ca.crt"), []byte("partial"), 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := LoadOrCreateAuthority(filepath.Join(directory, "ca.crt"), filepath.Join(directory, "ca.key")); err == nil {
		t.Fatal("partial proxy CA pair was accepted")
	}
}
