package config

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"net"
	"net/url"
	"os"
	"strconv"
	"strings"

	"gopkg.in/yaml.v3"
)

const (
	// APIVersion identifies the configuration schema understood by this binary.
	APIVersion = "owtf.dev/v1alpha1"
	// Kind is the required YAML document kind.
	Kind = "Config"
	// DefaultPath is the configuration file checked by server and proxy commands.
	DefaultPath = ".owtf/config.yaml"

	maximumFileSize = 1 << 20
)

// Config contains process settings. Plugin behavior and inputs belong in
// plugin manifests, not in this global configuration.
type Config struct {
	APIVersion string  `json:"api_version" yaml:"apiVersion"`
	Kind       string  `json:"kind" yaml:"kind"`
	LogLevel   string  `json:"log_level" yaml:"logLevel"`
	HTTP       HTTP    `json:"http" yaml:"http"`
	Server     Server  `json:"server" yaml:"server"`
	Plugins    Plugins `json:"plugins" yaml:"plugins"`
	Proxy      Proxy   `json:"proxy" yaml:"proxy"`
	AI         AI      `json:"ai" yaml:"ai"`
}

// HTTP configures OWTF-owned collectors, not external tools or proxy forwarding.
type HTTP struct {
	UserAgent             string `json:"user_agent" yaml:"userAgent"`
	RequestTimeoutSeconds int    `json:"request_timeout_seconds" yaml:"requestTimeoutSeconds"`
}

// Server configures the API process and bounded worker pool.
type Server struct {
	Address            string `json:"address" yaml:"address"`
	DataDirectory      string `json:"data_directory" yaml:"dataDirectory"`
	Workers            int    `json:"workers" yaml:"workers"`
	TaskTimeoutSeconds int    `json:"task_timeout_seconds" yaml:"taskTimeoutSeconds"`
}

// Plugins configures trusted manifest discovery and optional container runs.
type Plugins struct {
	Directory         string `json:"directory" yaml:"directory"`
	ProfilesDirectory string `json:"profiles_directory" yaml:"profilesDirectory"`
	WordlistDirectory string `json:"wordlist_directory" yaml:"wordlistDirectory"`
	DefaultProfile    string `json:"default_profile" yaml:"defaultProfile"`
	ContainerEngine   string `json:"container_engine" yaml:"containerEngine"`
}

// Proxy configures the standalone OWTF capture proxy.
type Proxy struct {
	ListenAddress       string   `json:"listen_address" yaml:"listenAddress"`
	APIAddress          string   `json:"api_address" yaml:"apiAddress"`
	Output              string   `json:"output" yaml:"output"`
	CACertificate       string   `json:"ca_certificate" yaml:"caCertificate"`
	CAKey               string   `json:"ca_key" yaml:"caKey"`
	MaximumBody         int64    `json:"maximum_body" yaml:"maximumBody"`
	MaximumTransactions int      `json:"maximum_transactions" yaml:"maximumTransactions"`
	Attempts            int      `json:"attempts" yaml:"attempts"`
	CacheEntries        int      `json:"cache_entries" yaml:"cacheEntries"`
	CacheMaximumBody    int64    `json:"cache_maximum_body" yaml:"cacheMaximumBody"`
	CookieBlacklist     []string `json:"cookie_blacklist" yaml:"cookieBlacklist"`
	CookieWhitelist     []string `json:"cookie_whitelist" yaml:"cookieWhitelist"`
	Upstream            string   `json:"upstream" yaml:"upstream"`
	HTTPAuthFile        string   `json:"http_auth_file" yaml:"httpAuthFile"`
	InterceptorFile     string   `json:"interceptor_file" yaml:"interceptorFile"`
	InsecureUpstream    bool     `json:"insecure_upstream" yaml:"insecureUpstream"`
	TargetHosts         []string `json:"target_hosts" yaml:"targetHosts"`
}

// Default returns a complete configuration with conservative local settings.
func Default() Config {
	return Config{
		APIVersion: APIVersion,
		Kind:       Kind,
		LogLevel:   "info",
		HTTP:       HTTP{UserAgent: "OWTF/0.1", RequestTimeoutSeconds: 20},
		Server: Server{
			Address: ":8009", DataDirectory: ".owtf", Workers: 1,
			TaskTimeoutSeconds: 30,
		},
		Plugins: Plugins{
			Directory: "plugins", ProfilesDirectory: "profiles",
			WordlistDirectory: "wordlists",
			DefaultProfile:    "default", ContainerEngine: "docker",
		},
		Proxy: Proxy{
			ListenAddress: "127.0.0.1:8008", APIAddress: "127.0.0.1:8010",
			Output: ".owtf/proxy/capture.har", CACertificate: ".owtf/proxy/ca.crt",
			CAKey: ".owtf/proxy/ca.key", MaximumBody: 1 << 20,
			MaximumTransactions: 10_000, Attempts: 3, CacheEntries: 1000,
			CacheMaximumBody: 1 << 20,
			CookieBlacklist:  []string{"_ga", "__utma", "__utmb", "__utmc", "__utmz", "__utmv"},
			CookieWhitelist:  []string{}, TargetHosts: []string{},
		},
	}
}

// Load reads one strict configuration document from path. Missing required
// schema fields, unknown fields, trailing documents, and unsafe secret storage
// are rejected.
func Load(path string) (Config, error) {
	file, err := os.Open(path)
	if err != nil {
		return Config{}, fmt.Errorf("open configuration: %w", err)
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil {
		return Config{}, fmt.Errorf("inspect configuration: %w", err)
	}
	if !info.Mode().IsRegular() {
		return Config{}, errors.New("configuration is not a regular file")
	}
	if info.Size() > maximumFileSize {
		return Config{}, fmt.Errorf("configuration exceeds %d bytes", maximumFileSize)
	}
	data, err := io.ReadAll(io.LimitReader(file, maximumFileSize+1))
	if err != nil {
		return Config{}, fmt.Errorf("read configuration: %w", err)
	}
	return Parse(data)
}

// Parse validates a strict YAML configuration without reading files or applying
// environment overrides. It is shared by file loading and API validation.
func Parse(data []byte) (Config, error) {
	if len(data) > maximumFileSize {
		return Config{}, fmt.Errorf("configuration exceeds %d bytes", maximumFileSize)
	}

	var header struct {
		APIVersion string `yaml:"apiVersion"`
		Kind       string `yaml:"kind"`
	}
	if err := yaml.Unmarshal(data, &header); err != nil {
		return Config{}, fmt.Errorf("decode configuration header: %w", err)
	}
	if header.APIVersion == "" || header.Kind == "" {
		return Config{}, errors.New("configuration requires apiVersion and kind")
	}

	result := Default()
	decoder := yaml.NewDecoder(bytes.NewReader(data))
	decoder.KnownFields(true)
	if err := decoder.Decode(&result); err != nil {
		return Config{}, fmt.Errorf("decode configuration: %w", err)
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		if err == nil {
			return Config{}, errors.New("configuration contains multiple YAML documents")
		}
		return Config{}, fmt.Errorf("decode configuration: %w", err)
	}
	if hasURLCredentials(result.Proxy.Upstream) {
		return Config{}, errors.New("proxy upstream credentials must come from the environment")
	}
	if err := result.Validate(); err != nil {
		return Config{}, err
	}
	return result, nil
}

// LoadOptional loads path when it exists and otherwise returns defaults.
func LoadOptional(path string) (Config, error) {
	result, err := Load(path)
	if errors.Is(err, os.ErrNotExist) {
		return Default(), nil
	}
	return result, err
}

// ApplyEnvironment overlays recognized environment variables atomically.
func (config *Config) ApplyEnvironment(lookup func(string) (string, bool)) error {
	if lookup == nil {
		return errors.New("environment lookup is required")
	}
	next := *config
	textValues := []struct {
		name        string
		destination *string
	}{
		{"OWTF_LOG_LEVEL", &next.LogLevel},
		{"OWTF_HTTP_USER_AGENT", &next.HTTP.UserAgent},
		{"OWTF_ADDR", &next.Server.Address},
		{"OWTF_DATA_DIR", &next.Server.DataDirectory},
		{"OWTF_PLUGIN_DIR", &next.Plugins.Directory},
		{"OWTF_PROFILE_DIR", &next.Plugins.ProfilesDirectory},
		{"OWTF_WORDLIST_DIR", &next.Plugins.WordlistDirectory},
		{"OWTF_PROFILE", &next.Plugins.DefaultProfile},
		{"OWTF_CONTAINER_ENGINE", &next.Plugins.ContainerEngine},
		{"OWTF_PROXY_LISTEN", &next.Proxy.ListenAddress},
		{"OWTF_PROXY_API_LISTEN", &next.Proxy.APIAddress},
		{"OWTF_PROXY_OUTPUT", &next.Proxy.Output},
		{"OWTF_PROXY_CA_CERT", &next.Proxy.CACertificate},
		{"OWTF_PROXY_CA_KEY", &next.Proxy.CAKey},
		{"OWTF_PROXY_UPSTREAM", &next.Proxy.Upstream},
		{"OWTF_PROXY_HTTP_AUTH_FILE", &next.Proxy.HTTPAuthFile},
		{"OWTF_PROXY_INTERCEPTOR_FILE", &next.Proxy.InterceptorFile},
	}
	for _, value := range textValues {
		if text, ok := lookup(value.name); ok {
			*value.destination = text
		}
	}
	integers := []struct {
		name        string
		destination *int
	}{
		{"OWTF_HTTP_REQUEST_TIMEOUT", &next.HTTP.RequestTimeoutSeconds},
		{"OWTF_WORKERS", &next.Server.Workers},
		{"OWTF_TASK_TIMEOUT", &next.Server.TaskTimeoutSeconds},
		{"OWTF_PROXY_MAX_TRANSACTIONS", &next.Proxy.MaximumTransactions},
		{"OWTF_PROXY_ATTEMPTS", &next.Proxy.Attempts},
		{"OWTF_PROXY_CACHE_ENTRIES", &next.Proxy.CacheEntries},
	}
	for _, value := range integers {
		if text, ok := lookup(value.name); ok {
			parsed, err := strconv.Atoi(text)
			if err != nil {
				return fmt.Errorf("%s must be an integer", value.name)
			}
			*value.destination = parsed
		}
	}
	int64s := []struct {
		name        string
		destination *int64
	}{
		{"OWTF_PROXY_MAX_BODY", &next.Proxy.MaximumBody},
		{"OWTF_PROXY_CACHE_MAX_BODY", &next.Proxy.CacheMaximumBody},
	}
	for _, value := range int64s {
		if text, ok := lookup(value.name); ok {
			parsed, err := strconv.ParseInt(text, 10, 64)
			if err != nil {
				return fmt.Errorf("%s must be an integer", value.name)
			}
			*value.destination = parsed
		}
	}
	if text, ok := lookup("OWTF_PROXY_INSECURE_UPSTREAM"); ok {
		parsed, err := strconv.ParseBool(text)
		if err != nil {
			return errors.New("OWTF_PROXY_INSECURE_UPSTREAM must be a boolean")
		}
		next.Proxy.InsecureUpstream = parsed
	}
	listValues := []struct {
		name        string
		destination *[]string
	}{
		{"OWTF_PROXY_COOKIE_BLACKLIST", &next.Proxy.CookieBlacklist},
		{"OWTF_PROXY_COOKIE_WHITELIST", &next.Proxy.CookieWhitelist},
		{"OWTF_PROXY_TARGET_HOSTS", &next.Proxy.TargetHosts},
	}
	for _, value := range listValues {
		if text, ok := lookup(value.name); ok {
			*value.destination = splitList(text)
		}
	}
	if err := next.Validate(); err != nil {
		return err
	}
	*config = next
	return nil
}

// Validate checks all process settings before listeners or workers start.
func (config Config) Validate() error {
	switch config.LogLevel {
	case "debug", "info", "warn", "error":
	default:
		return errors.New("logLevel must be debug, info, warn, or error")
	}
	if strings.TrimSpace(config.HTTP.UserAgent) == "" {
		return errors.New("http.userAgent cannot be empty")
	}
	for _, c := range config.HTTP.UserAgent {
		if c < 32 || c == 127 {
			return errors.New("http.userAgent cannot contain control characters")
		}
	}
	if config.HTTP.RequestTimeoutSeconds < 1 || config.HTTP.RequestTimeoutSeconds > 86400 {
		return errors.New("http.requestTimeoutSeconds must be between 1 and 86400")
	}
	if config.APIVersion != APIVersion {

		return fmt.Errorf("unsupported apiVersion %q", config.APIVersion)
	}
	if config.Kind != Kind {
		return fmt.Errorf("unsupported configuration kind %q", config.Kind)
	}
	if err := listenAddress("server.address", config.Server.Address); err != nil {
		return err
	}
	if err := textValue("server.dataDirectory", config.Server.DataDirectory); err != nil {
		return err
	}
	if config.Server.Workers < 1 || config.Server.Workers > 64 {
		return errors.New("server.workers must be between 1 and 64")
	}
	if config.Server.TaskTimeoutSeconds < 1 || config.Server.TaskTimeoutSeconds > 86_400 {
		return errors.New("server.taskTimeoutSeconds must be between 1 and 86400")
	}
	if err := textValue("plugins.directory", config.Plugins.Directory); err != nil {
		return err
	}
	if err := textValue("plugins.profilesDirectory", config.Plugins.ProfilesDirectory); err != nil {
		return err
	}
	if err := textValue("plugins.wordlistDirectory", config.Plugins.WordlistDirectory); err != nil {
		return err
	}
	if err := textValue("plugins.defaultProfile", config.Plugins.DefaultProfile); err != nil {
		return err
	}
	if err := textValue("plugins.containerEngine", config.Plugins.ContainerEngine); err != nil {
		return err
	}
	if err := listenAddress("proxy.listenAddress", config.Proxy.ListenAddress); err != nil {
		return err
	}
	if err := listenAddress("proxy.apiAddress", config.Proxy.APIAddress); err != nil {
		return err
	}
	for _, field := range []struct {
		name  string
		value string
	}{
		{"proxy.output", config.Proxy.Output},
		{"proxy.caCertificate", config.Proxy.CACertificate},
		{"proxy.caKey", config.Proxy.CAKey},
	} {
		if err := textValue(field.name, field.value); err != nil {
			return err
		}
	}
	if config.Proxy.MaximumBody < 1 || config.Proxy.MaximumBody > 64<<20 {
		return errors.New("proxy.maximumBody must be between 1 and 67108864")
	}
	if config.Proxy.MaximumTransactions < 1 || config.Proxy.MaximumTransactions > 1_000_000 {
		return errors.New("proxy.maximumTransactions must be between 1 and 1000000")
	}
	if config.Proxy.Attempts < 1 || config.Proxy.Attempts > 10 {
		return errors.New("proxy.attempts must be between 1 and 10")
	}
	if config.Proxy.CacheEntries < 0 || config.Proxy.CacheEntries > 100_000 {
		return errors.New("proxy.cacheEntries must be between 0 and 100000")
	}
	if config.Proxy.CacheMaximumBody < 1 || config.Proxy.CacheMaximumBody > 64<<20 {
		return errors.New("proxy.cacheMaximumBody must be between 1 and 67108864")
	}
	if err := upstreamURL(config.Proxy.Upstream); err != nil {
		return err
	}
	for _, field := range []struct {
		name  string
		value string
	}{
		{"proxy.httpAuthFile", config.Proxy.HTTPAuthFile},
		{"proxy.interceptorFile", config.Proxy.InterceptorFile},
	} {
		if strings.IndexByte(field.value, 0) >= 0 {
			return fmt.Errorf("%s contains a NUL byte", field.name)
		}
	}
	for _, list := range []struct {
		name   string
		values []string
	}{
		{"proxy.cookieBlacklist", config.Proxy.CookieBlacklist},
		{"proxy.cookieWhitelist", config.Proxy.CookieWhitelist},
		{"proxy.targetHosts", config.Proxy.TargetHosts},
	} {
		for _, value := range list.values {
			if strings.TrimSpace(value) == "" || strings.IndexByte(value, 0) >= 0 {
				return fmt.Errorf("%s contains an empty or invalid value", list.name)
			}
		}
	}
	return config.AI.Validate()
}

// Redacted returns a copy safe to print. An upstream username and password are
// replaced even when they came from an environment variable.
func (config Config) Redacted() Config {
	if parsed, err := url.Parse(config.Proxy.Upstream); err == nil && parsed.User != nil {
		parsed.User = url.User("redacted")
		config.Proxy.Upstream = parsed.String()
	}
	return config
}

func listenAddress(name, value string) error {
	_, port, err := net.SplitHostPort(value)
	if err != nil {
		return fmt.Errorf("%s is invalid: %w", name, err)
	}
	number, err := strconv.ParseUint(port, 10, 16)
	if err != nil || number > 65_535 {
		return fmt.Errorf("%s has an invalid port", name)
	}
	return nil
}

func textValue(name, value string) error {
	if strings.TrimSpace(value) == "" {
		return fmt.Errorf("%s cannot be empty", name)
	}
	if strings.IndexByte(value, 0) >= 0 {
		return fmt.Errorf("%s contains a NUL byte", name)
	}
	return nil
}

func upstreamURL(value string) error {
	if value == "" {
		return nil
	}
	parsed, err := url.Parse(value)
	if err != nil || parsed.Host == "" {
		return fmt.Errorf("proxy.upstream is invalid")
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" && parsed.Scheme != "socks5" && parsed.Scheme != "socks5h" {
		return fmt.Errorf("proxy.upstream has unsupported scheme %q", parsed.Scheme)
	}
	if (parsed.Path != "" && parsed.Path != "/") || parsed.RawQuery != "" || parsed.Fragment != "" {
		return errors.New("proxy.upstream cannot contain a path, query, or fragment")
	}
	return nil
}

func hasURLCredentials(value string) bool {
	parsed, err := url.Parse(value)
	return err == nil && parsed.User != nil
}

func splitList(value string) []string {
	if strings.TrimSpace(value) == "" {
		return []string{}
	}
	result := make([]string, 0, strings.Count(value, ",")+1)
	for _, item := range strings.Split(value, ",") {
		if item = strings.TrimSpace(item); item != "" {
			result = append(result, item)
		}
	}
	return result
}
