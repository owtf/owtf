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
	"strings"
	"syscall"
	"time"

	owtfconfig "github.com/owtf/owtf/internal/config"
	owtfproxy "github.com/owtf/owtf/internal/proxy"
)

type stringFlags struct {
	values  []string
	changed bool
}

func (values *stringFlags) String() string { return strings.Join(values.values, ",") }
func (values *stringFlags) Set(value string) error {
	value = strings.TrimSpace(value)
	if value == "" {
		return errors.New("value cannot be empty")
	}
	if !values.changed {
		values.values = nil
		values.changed = true
	}
	values.values = append(values.values, value)
	return nil
}

func runProxy(parent context.Context, args []string, stdout, stderr io.Writer) error {
	settings, err := proxyConfiguration(args, stderr)
	if err != nil {
		return err
	}
	proxySettings := settings.Proxy

	authority, err := owtfproxy.LoadOrCreateAuthority(proxySettings.CACertificate, proxySettings.CAKey)
	if err != nil {
		return err
	}
	transport := http.DefaultTransport.(*http.Transport).Clone()
	defer transport.CloseIdleConnections()
	transport.DisableCompression = true
	transport.Proxy = nil
	transport.TLSClientConfig = &tls.Config{MinVersion: tls.VersionTLS12, InsecureSkipVerify: proxySettings.InsecureUpstream}
	if proxySettings.Upstream != "" {
		if err := owtfproxy.SetUpstream(transport, proxySettings.Upstream); err != nil {
			return err
		}
	}
	var upstreamTransport http.RoundTripper = transport
	if proxySettings.HTTPAuthFile != "" {
		credentials, err := loadHTTPCredentials(proxySettings.HTTPAuthFile)
		if err != nil {
			return err
		}
		upstreamTransport, err = owtfproxy.NewOriginAuthTransport(upstreamTransport, credentials)
		if err != nil {
			return err
		}
	}
	var roundTripper http.RoundTripper = owtfproxy.RetryTransport{
		Next: upstreamTransport, MaxAttempts: proxySettings.Attempts, Delay: 100 * time.Millisecond,
	}
	if proxySettings.CacheEntries > 0 {
		cache, err := owtfproxy.NewResponseCache(owtfproxy.CacheOptions{
			MaximumEntries: proxySettings.CacheEntries, MaximumBody: proxySettings.CacheMaximumBody,
			CookieBlacklist: proxySettings.CookieBlacklist, CookieWhitelist: proxySettings.CookieWhitelist,
		})
		if err != nil {
			return err
		}
		roundTripper = cache.RoundTripper(roundTripper)
	}

	recorder := owtfproxy.NewRecorder(proxySettings.MaximumTransactions)
	live, err := owtfproxy.NewLiveInterception(proxySettings.MaximumBody, 0)
	if err != nil {
		return err
	}
	defer live.Close()
	interceptors, err := owtfproxy.NewInterceptors(nil, proxySettings.MaximumBody)
	if err != nil {
		return err
	}
	if proxySettings.InterceptorFile != "" {
		file, err := os.Open(proxySettings.InterceptorFile)
		if err != nil {
			return fmt.Errorf("open interceptor file: %w", err)
		}
		interceptors, err = owtfproxy.LoadInterceptors(file, proxySettings.MaximumBody)
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
		AllowedHosts: proxySettings.TargetHosts, MaximumBody: proxySettings.MaximumBody,
		Interceptors: interceptors, Live: live,
		ErrorLog: log.New(stderr, "proxy: ", log.LstdFlags),
	})
	if err != nil {
		return err
	}
	listener, err := net.Listen("tcp", proxySettings.ListenAddress)
	if err != nil {
		return fmt.Errorf("listen for proxy traffic: %w", err)
	}
	apiListener, err := net.Listen("tcp", proxySettings.APIAddress)
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
		Authority: authority, Recorder: recorder, RepeatClient: repeatClient,
		Interceptors: interceptors, Live: live, MaximumBody: proxySettings.MaximumBody,
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
		"ca_certificate": proxySettings.CACertificate, "output": proxySettings.Output,
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
	live.Close()
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
	return errors.Join(runErr, shutdownErr, recorder.WriteHAR(proxySettings.Output))
}

func proxyConfiguration(args []string, stderr io.Writer) (owtfconfig.Config, error) {
	path, err := configurationPath(args)
	if err != nil {
		return owtfconfig.Config{}, err
	}
	settings, err := effectiveConfiguration(path)
	if err != nil {
		return owtfconfig.Config{}, err
	}
	proxySettings := &settings.Proxy
	flags := flag.NewFlagSet("owtf proxy", flag.ContinueOnError)
	flags.SetOutput(stderr)
	flags.String("config", path, "configuration file")
	flags.StringVar(&proxySettings.ListenAddress, "listen", proxySettings.ListenAddress, "proxy listen address")
	flags.StringVar(&proxySettings.APIAddress, "api-listen", proxySettings.APIAddress, "proxy API listen address")
	flags.StringVar(&proxySettings.Output, "output", proxySettings.Output, "HAR output path")
	flags.StringVar(&proxySettings.CACertificate, "ca-cert", proxySettings.CACertificate, "proxy CA certificate path")
	flags.StringVar(&proxySettings.CAKey, "ca-key", proxySettings.CAKey, "proxy CA private key path")
	flags.Int64Var(&proxySettings.MaximumBody, "max-body", proxySettings.MaximumBody, "maximum captured bytes per request or response body")
	flags.IntVar(&proxySettings.MaximumTransactions, "max-transactions", proxySettings.MaximumTransactions, "maximum retained transactions")
	flags.IntVar(&proxySettings.Attempts, "attempts", proxySettings.Attempts, "maximum attempts for transport failures and HTTP 408/599")
	flags.IntVar(&proxySettings.CacheEntries, "cache-entries", proxySettings.CacheEntries, "maximum cached responses; zero disables the cache")
	flags.Int64Var(&proxySettings.CacheMaximumBody, "cache-max-body", proxySettings.CacheMaximumBody, "maximum response body bytes stored per cache entry")
	cookieBlacklist := strings.Join(proxySettings.CookieBlacklist, ",")
	cookieWhitelist := strings.Join(proxySettings.CookieWhitelist, ",")
	flags.StringVar(&cookieBlacklist, "cookie-blacklist", cookieBlacklist, "comma-separated cookies excluded from cache identity")
	flags.StringVar(&cookieWhitelist, "cookie-whitelist", cookieWhitelist, "comma-separated cookies allowed in cache identity")
	flags.StringVar(&proxySettings.Upstream, "upstream", proxySettings.Upstream, "optional HTTP, HTTPS, or SOCKS5 proxy URL")
	flags.StringVar(&proxySettings.HTTPAuthFile, "http-auth-file", proxySettings.HTTPAuthFile, "JSON file containing target-host HTTP credentials")
	flags.StringVar(&proxySettings.InterceptorFile, "interceptor-file", proxySettings.InterceptorFile, "JSON file containing static interceptor rules")
	flags.BoolVar(&proxySettings.InsecureUpstream, "insecure-upstream", proxySettings.InsecureUpstream, "allow invalid upstream TLS certificates")
	targetHosts := stringFlags{values: append([]string(nil), proxySettings.TargetHosts...)}
	flags.Var(&targetHosts, "target-host", "allowed target host; repeat to allow more than one")
	if err := flags.Parse(args); err != nil {
		return owtfconfig.Config{}, err
	}
	if flags.NArg() != 0 {
		return owtfconfig.Config{}, errors.New("proxy accepts no positional arguments")
	}
	proxySettings.CookieBlacklist = splitNames(cookieBlacklist)
	proxySettings.CookieWhitelist = splitNames(cookieWhitelist)
	proxySettings.TargetHosts = targetHosts.values
	if err := settings.Validate(); err != nil {
		return owtfconfig.Config{}, err
	}
	return settings, nil
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
