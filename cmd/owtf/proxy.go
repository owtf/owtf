package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
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
	apiAddress := flags.String("api-listen", "127.0.0.1:8010", "proxy API listen address")
	outputPath := flags.String("output", filepath.Join(".owtf", "proxy", "capture.har"), "HAR output path")
	certificatePath := flags.String("ca-cert", filepath.Join(".owtf", "proxy", "ca.crt"), "proxy CA certificate path")
	keyPath := flags.String("ca-key", filepath.Join(".owtf", "proxy", "ca.key"), "proxy CA private key path")
	maximumBody := flags.Int64("max-body", 1<<20, "maximum captured bytes per request or response body")
	maximumTransactions := flags.Int("max-transactions", 10_000, "maximum retained transactions")
	maximumAttempts := flags.Int("attempts", 3, "maximum attempts for transport failures and HTTP 408/599")
	cacheEntries := flags.Int("cache-entries", 1000, "maximum cached responses; zero disables the cache")
	cacheBody := flags.Int64("cache-max-body", 1<<20, "maximum response body bytes stored per cache entry")
	cookieBlacklist := flags.String("cookie-blacklist", "_ga,__utma,__utmb,__utmc,__utmz,__utmv", "comma-separated cookies excluded from cache identity")
	cookieWhitelist := flags.String("cookie-whitelist", "", "comma-separated cookies allowed in cache identity")
	upstream := flags.String("upstream", "", "optional HTTP, HTTPS, or SOCKS5 proxy URL")
	httpAuthFile := flags.String("http-auth-file", "", "JSON file containing target-host HTTP credentials")
	interceptorFile := flags.String("interceptor-file", "", "JSON file containing static interceptor rules")
	insecureUpstream := flags.Bool("insecure-upstream", false, "allow invalid upstream TLS certificates")
	var targetHosts stringFlags
	flags.Var(&targetHosts, "target-host", "allowed target host; repeat to allow more than one")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("proxy accepts no positional arguments")
	}
	if *maximumBody < 1 || *maximumTransactions < 1 || *maximumAttempts < 1 || *cacheEntries < 0 || *cacheBody < 1 {
		return errors.New("proxy limits are invalid")
	}

	authority, err := owtfproxy.LoadOrCreateAuthority(*certificatePath, *keyPath)
	if err != nil {
		return err
	}
	transport := http.DefaultTransport.(*http.Transport).Clone()
	defer transport.CloseIdleConnections()
	transport.DisableCompression = true
	transport.Proxy = nil
	transport.TLSClientConfig = &tls.Config{MinVersion: tls.VersionTLS12, InsecureSkipVerify: *insecureUpstream}
	if *upstream != "" {
		if err := owtfproxy.SetUpstream(transport, *upstream); err != nil {
			return err
		}
	}
	var upstreamTransport http.RoundTripper = transport
	if *httpAuthFile != "" {
		credentials, err := loadHTTPCredentials(*httpAuthFile)
		if err != nil {
			return err
		}
		upstreamTransport, err = owtfproxy.NewOriginAuthTransport(upstreamTransport, credentials)
		if err != nil {
			return err
		}
	}
	var roundTripper http.RoundTripper = owtfproxy.RetryTransport{
		Next: upstreamTransport, MaxAttempts: *maximumAttempts, Delay: 100 * time.Millisecond,
	}
	if *cacheEntries > 0 {
		cache, err := owtfproxy.NewResponseCache(owtfproxy.CacheOptions{
			MaximumEntries: *cacheEntries, MaximumBody: *cacheBody,
			CookieBlacklist: splitNames(*cookieBlacklist), CookieWhitelist: splitNames(*cookieWhitelist),
		})
		if err != nil {
			return err
		}
		roundTripper = cache.RoundTripper(roundTripper)
	}

	recorder := owtfproxy.NewRecorder(*maximumTransactions)
	var interceptors *owtfproxy.Interceptors
	if *interceptorFile != "" {
		file, err := os.Open(*interceptorFile)
		if err != nil {
			return fmt.Errorf("open interceptor file: %w", err)
		}
		interceptors, err = owtfproxy.LoadInterceptors(file, *maximumBody)
		closeErr := file.Close()
		if err != nil {
			return err
		}
		if closeErr != nil {
			return fmt.Errorf("close interceptor file: %w", closeErr)
		}
	}
	handler, err := owtfproxy.New(owtfproxy.Config{
		Authority: authority, Recorder: recorder, Transport: roundTripper,
		AllowedHosts: targetHosts, MaximumBody: *maximumBody,
		Interceptors: interceptors,
		ErrorLog:     log.New(stderr, "proxy: ", log.LstdFlags),
	})
	if err != nil {
		return err
	}
	listener, err := net.Listen("tcp", *listenAddress)
	if err != nil {
		return fmt.Errorf("listen for proxy traffic: %w", err)
	}
	apiListener, err := net.Listen("tcp", *apiAddress)
	if err != nil {
		listener.Close()
		return fmt.Errorf("listen for proxy API: %w", err)
	}
	proxyURL := &url.URL{Scheme: "http", Host: listener.Addr().String()}
	roots := x509.NewCertPool()
	if !roots.AppendCertsFromPEM(authority.CertificatePEM()) {
		listener.Close()
		apiListener.Close()
		return errors.New("load proxy CA for repeater")
	}
	repeatTransport := http.DefaultTransport.(*http.Transport).Clone()
	defer repeatTransport.CloseIdleConnections()
	repeatTransport.DisableCompression = true
	repeatTransport.Proxy = http.ProxyURL(proxyURL)
	repeatTransport.TLSClientConfig = &tls.Config{MinVersion: tls.VersionTLS12, RootCAs: roots}
	repeatClient := &http.Client{
		Transport: repeatTransport, Timeout: 2 * time.Minute,
		CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse },
	}
	apiHandler, err := owtfproxy.NewAPI(owtfproxy.APIConfig{
		Authority: authority, Recorder: recorder, RepeatClient: repeatClient, MaximumBody: *maximumBody,
	})
	if err != nil {
		listener.Close()
		apiListener.Close()
		return err
	}
	server := &http.Server{
		Handler: handler, ReadHeaderTimeout: 10 * time.Second, IdleTimeout: 60 * time.Second,
		ErrorLog: log.New(stderr, "proxy: ", log.LstdFlags),
	}
	apiServer := &http.Server{
		Handler: apiHandler, ReadHeaderTimeout: 5 * time.Second, IdleTimeout: 30 * time.Second,
		ErrorLog: log.New(stderr, "proxy API: ", log.LstdFlags),
	}
	ctx, stop := signal.NotifyContext(parent, os.Interrupt, syscall.SIGTERM)
	defer stop()
	if err := json.NewEncoder(stdout).Encode(map[string]any{
		"listen": listener.Addr().String(), "api": apiListener.Addr().String(),
		"ca_certificate": *certificatePath, "output": *outputPath,
	}); err != nil {
		listener.Close()
		apiListener.Close()
		return fmt.Errorf("write proxy status: %w", err)
	}
	type serverResult struct {
		name string
		err  error
	}
	results := make(chan serverResult, 2)
	go func() { results <- serverResult{name: "proxy", err: server.Serve(listener)} }()
	go func() { results <- serverResult{name: "proxy API", err: apiServer.Serve(apiListener)} }()

	received := 0
	var runErr error
	select {
	case <-ctx.Done():
	case result := <-results:
		received++
		if result.err != nil && !errors.Is(result.err, http.ErrServerClosed) {
			runErr = fmt.Errorf("%s server: %w", result.name, result.err)
		}
	}
	stop()
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	shutdownErr := shutdownHTTPServers(shutdownCtx, server, apiServer)
	for received < 2 {
		result := <-results
		received++
		if result.err != nil && !errors.Is(result.err, http.ErrServerClosed) {
			runErr = errors.Join(runErr, fmt.Errorf("%s server: %w", result.name, result.err))
		}
	}
	return errors.Join(runErr, shutdownErr, recorder.WriteHAR(*outputPath))
}

func shutdownHTTPServers(ctx context.Context, servers ...*http.Server) error {
	results := make(chan error, len(servers))
	for _, server := range servers {
		go func() {
			err := server.Shutdown(ctx)
			if err != nil {
				err = errors.Join(err, server.Close())
			}
			results <- err
		}()
	}
	var result error
	for range servers {
		result = errors.Join(result, <-results)
	}
	return result
}

func splitNames(value string) []string {
	var result []string
	for _, item := range strings.Split(value, ",") {
		if item = strings.TrimSpace(item); item != "" {
			result = append(result, item)
		}
	}
	return result
}

func loadHTTPCredentials(path string) (map[string]owtfproxy.Credentials, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open HTTP authentication file: %w", err)
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil {
		return nil, fmt.Errorf("inspect HTTP authentication file: %w", err)
	}
	if !info.Mode().IsRegular() {
		return nil, errors.New("HTTP authentication file is not a regular file")
	}
	if info.Size() > 64<<10 {
		return nil, errors.New("HTTP authentication file exceeds 64 KiB")
	}
	if info.Mode().Perm()&0o077 != 0 {
		return nil, errors.New("HTTP authentication file must not be accessible by group or other users")
	}
	decoder := json.NewDecoder(io.LimitReader(file, 64<<10))
	decoder.DisallowUnknownFields()
	credentials := make(map[string]owtfproxy.Credentials)
	if err := decoder.Decode(&credentials); err != nil {
		return nil, fmt.Errorf("decode HTTP authentication file: %w", err)
	}
	if len(credentials) > 1000 {
		return nil, errors.New("HTTP authentication file contains more than 1000 hosts")
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		if err == nil {
			return nil, errors.New("HTTP authentication file contains multiple JSON values")
		}
		return nil, fmt.Errorf("decode HTTP authentication file: %w", err)
	}
	return credentials, nil
}
