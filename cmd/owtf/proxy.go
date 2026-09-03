package main

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	owtfproxy "github.com/owtf/owtf/internal/proxy"
)

type stringFlags []string

func (values *stringFlags) String() string { return strings.Join(*values, ",") }
func (values *stringFlags) Set(value string) error {
	value = strings.TrimSpace(value)
	if value == "" {
		return errors.New("value cannot be empty")
	}
	*values = append(*values, value)
	return nil
}

func runProxy(parent context.Context, args []string, stdout, stderr io.Writer) error {
	flags := flag.NewFlagSet("owtf proxy", flag.ContinueOnError)
	flags.SetOutput(stderr)
	listenAddress := flags.String("listen", "127.0.0.1:8008", "proxy listen address")
	outputPath := flags.String("output", filepath.Join(".owtf", "proxy", "capture.har"), "HAR output path")
	certificatePath := flags.String("ca-cert", filepath.Join(".owtf", "proxy", "ca.crt"), "proxy CA certificate path")
	keyPath := flags.String("ca-key", filepath.Join(".owtf", "proxy", "ca.key"), "proxy CA private key path")
	maximumBody := flags.Int64("max-body", 1<<20, "maximum captured bytes per request or response body")
	maximumTransactions := flags.Int("max-transactions", 10_000, "maximum retained transactions")
	upstream := flags.String("upstream", "", "optional outbound HTTP proxy URL")
	insecureUpstream := flags.Bool("insecure-upstream", false, "allow invalid upstream TLS certificates")
	var targetHosts stringFlags
	flags.Var(&targetHosts, "target-host", "allowed target host; repeat to allow more than one")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("proxy accepts no positional arguments")
	}
	if *maximumBody < 1 || *maximumTransactions < 1 {
		return errors.New("max-body and max-transactions must be positive")
	}

	authority, err := owtfproxy.LoadOrCreateAuthority(*certificatePath, *keyPath)
	if err != nil {
		return err
	}
	transport := http.DefaultTransport.(*http.Transport).Clone()
	transport.DisableCompression = true
	transport.Proxy = nil
	transport.TLSClientConfig = &tls.Config{MinVersion: tls.VersionTLS12, InsecureSkipVerify: *insecureUpstream}
	if *upstream != "" {
		proxyURL, err := url.Parse(*upstream)
		if err != nil || (proxyURL.Scheme != "http" && proxyURL.Scheme != "https") || proxyURL.Host == "" {
			return fmt.Errorf("invalid outbound HTTP proxy URL %q", *upstream)
		}
		transport.Proxy = http.ProxyURL(proxyURL)
	}

	recorder := owtfproxy.NewRecorder(*maximumTransactions)
	handler, err := owtfproxy.New(owtfproxy.Config{
		Authority: authority, Recorder: recorder, Transport: transport,
		AllowedHosts: targetHosts, MaximumBody: *maximumBody,
		ErrorLog: log.New(stderr, "proxy: ", log.LstdFlags),
	})
	if err != nil {
		return err
	}
	listener, err := net.Listen("tcp", *listenAddress)
	if err != nil {
		return fmt.Errorf("listen for proxy traffic: %w", err)
	}
	server := &http.Server{
		Handler: handler, ReadHeaderTimeout: 10 * time.Second, IdleTimeout: 60 * time.Second,
		ErrorLog: log.New(stderr, "proxy: ", log.LstdFlags),
	}
	ctx, stop := signal.NotifyContext(parent, os.Interrupt, syscall.SIGTERM)
	defer stop()
	go func() {
		<-ctx.Done()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = server.Shutdown(shutdownCtx)
	}()
	if err := json.NewEncoder(stdout).Encode(map[string]any{
		"listen": listener.Addr().String(), "ca_certificate": *certificatePath, "output": *outputPath,
	}); err != nil {
		listener.Close()
		return fmt.Errorf("write proxy status: %w", err)
	}
	serveErr := server.Serve(listener)
	if err := recorder.WriteHAR(*outputPath); err != nil {
		return err
	}
	if serveErr != nil && !errors.Is(serveErr, http.ErrServerClosed) {
		return serveErr
	}
	return nil
}
