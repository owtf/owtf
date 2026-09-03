package proxy

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"errors"
	"fmt"
	"math/big"
	"net"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// Authority signs the short-lived certificates used for HTTPS interception.
type Authority struct {
	certificate    *x509.Certificate
	key            *ecdsa.PrivateKey
	certificatePEM []byte
	mu             sync.Mutex
	cache          map[string]tls.Certificate
}

// LoadOrCreateAuthority loads a CA pair or creates it when both files are
// absent. A partial pair is rejected rather than silently replacing trust.
func LoadOrCreateAuthority(certificatePath, keyPath string) (*Authority, error) {
	certificatePEM, certificateErr := os.ReadFile(certificatePath)
	keyPEM, keyErr := os.ReadFile(keyPath)
	switch {
	case certificateErr == nil && keyErr == nil:
		return parseAuthority(certificatePEM, keyPEM)
	case errors.Is(certificateErr, os.ErrNotExist) && errors.Is(keyErr, os.ErrNotExist):
		certificatePEM, keyPEM, err := generateAuthority()
		if err != nil {
			return nil, err
		}
		if err := writePrivateFile(keyPath, keyPEM, 0o600); err != nil {
			return nil, fmt.Errorf("write proxy CA key: %w", err)
		}
		if err := writePrivateFile(certificatePath, certificatePEM, 0o644); err != nil {
			return nil, fmt.Errorf("write proxy CA certificate: %w", err)
		}
		return parseAuthority(certificatePEM, keyPEM)
	default:
		return nil, errors.New("proxy CA certificate and key must either both exist or both be absent")
	}
}

// CertificatePEM returns a copy of the public CA certificate.
func (a *Authority) CertificatePEM() []byte {
	return append([]byte(nil), a.certificatePEM...)
}

func (a *Authority) certificateForHost(host string) (tls.Certificate, error) {
	a.mu.Lock()
	defer a.mu.Unlock()
	if certificate, ok := a.cache[host]; ok {
		return certificate, nil
	}
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("generate host key: %w", err)
	}
	serial, err := randomSerial()
	if err != nil {
		return tls.Certificate{}, err
	}
	now := time.Now().UTC()
	template := &x509.Certificate{
		SerialNumber: serial,
		Subject:      pkix.Name{CommonName: host, Organization: []string{"OWTF Interception"}},
		NotBefore:    now.Add(-5 * time.Minute),
		NotAfter:     minimumTime(now.Add(365*24*time.Hour), a.certificate.NotAfter),
		KeyUsage:     x509.KeyUsageDigitalSignature,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}
	if address := net.ParseIP(host); address != nil {
		template.IPAddresses = []net.IP{address}
	} else {
		template.DNSNames = []string{host}
	}
	der, err := x509.CreateCertificate(rand.Reader, template, a.certificate, &key.PublicKey, a.key)
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("sign host certificate: %w", err)
	}
	keyBytes, err := x509.MarshalECPrivateKey(key)
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("marshal host key: %w", err)
	}
	certificatePEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "EC PRIVATE KEY", Bytes: keyBytes})
	certificate, err := tls.X509KeyPair(certificatePEM, keyPEM)
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("load host certificate: %w", err)
	}
	a.cache[host] = certificate
	return certificate, nil
}

func generateAuthority() ([]byte, []byte, error) {
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return nil, nil, fmt.Errorf("generate proxy CA key: %w", err)
	}
	serial, err := randomSerial()
	if err != nil {
		return nil, nil, err
	}
	now := time.Now().UTC()
	template := &x509.Certificate{
		SerialNumber:          serial,
		Subject:               pkix.Name{CommonName: "OWTF Proxy CA", Organization: []string{"OWTF"}},
		NotBefore:             now.Add(-5 * time.Minute),
		NotAfter:              now.Add(10 * 365 * 24 * time.Hour),
		IsCA:                  true,
		BasicConstraintsValid: true,
		KeyUsage:              x509.KeyUsageCertSign | x509.KeyUsageCRLSign | x509.KeyUsageDigitalSignature,
	}
	der, err := x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
	if err != nil {
		return nil, nil, fmt.Errorf("create proxy CA certificate: %w", err)
	}
	keyBytes, err := x509.MarshalECPrivateKey(key)
	if err != nil {
		return nil, nil, fmt.Errorf("marshal proxy CA key: %w", err)
	}
	return pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der}),
		pem.EncodeToMemory(&pem.Block{Type: "EC PRIVATE KEY", Bytes: keyBytes}), nil
}

func parseAuthority(certificatePEM, keyPEM []byte) (*Authority, error) {
	pair, err := tls.X509KeyPair(certificatePEM, keyPEM)
	if err != nil {
		return nil, fmt.Errorf("load proxy CA pair: %w", err)
	}
	if len(pair.Certificate) == 0 {
		return nil, errors.New("proxy CA certificate is empty")
	}
	certificate, err := x509.ParseCertificate(pair.Certificate[0])
	if err != nil {
		return nil, fmt.Errorf("parse proxy CA certificate: %w", err)
	}
	key, ok := pair.PrivateKey.(*ecdsa.PrivateKey)
	if !ok || !certificate.IsCA {
		return nil, errors.New("proxy CA must contain an ECDSA CA certificate and key")
	}
	return &Authority{
		certificate: certificate, key: key, certificatePEM: append([]byte(nil), certificatePEM...),
		cache: make(map[string]tls.Certificate),
	}, nil
}

func randomSerial() (*big.Int, error) {
	limit := new(big.Int).Lsh(big.NewInt(1), 128)
	serial, err := rand.Int(rand.Reader, limit)
	if err != nil {
		return nil, fmt.Errorf("generate certificate serial: %w", err)
	}
	return serial, nil
}

func minimumTime(left, right time.Time) time.Time {
	if left.Before(right) {
		return left
	}
	return right
}

func writePrivateFile(path string, data []byte, mode os.FileMode) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	temporary, err := os.CreateTemp(filepath.Dir(path), ".owtf-ca-*")
	if err != nil {
		return err
	}
	temporaryPath := temporary.Name()
	defer os.Remove(temporaryPath)
	if err := temporary.Chmod(mode); err != nil {
		temporary.Close()
		return err
	}
	if _, err := temporary.Write(data); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Close(); err != nil {
		return err
	}
	return os.Rename(temporaryPath, path)
}
