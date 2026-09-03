package main

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	owtfproxy "github.com/owtf/owtf/internal/proxy"
)

const (
	defaultProxyAPIURL = "http://127.0.0.1:8010"
	maximumCLIDataFile = 16 << 20
)

type proxyAPIOptions struct {
	address string
	timeout time.Duration
}

func (options *proxyAPIOptions) bind(flags *flag.FlagSet, timeout time.Duration) {
	flags.StringVar(&options.address, "api", env("OWTF_PROXY_API_URL", defaultProxyAPIURL), "proxy API URL")
	flags.DurationVar(&options.timeout, "timeout", timeout, "HTTP request timeout")
}

type proxyAPIClient struct {
	baseURL *url.URL
	client  *http.Client
	output  io.Writer
}

type headerFlags http.Header

func (headers *headerFlags) String() string {
	return fmt.Sprint(http.Header(*headers))
}

func (headers *headerFlags) Set(value string) error {
	name, value, ok := strings.Cut(value, ":")
	name = strings.TrimSpace(name)
	value = strings.TrimSpace(value)
	if !ok || name == "" {
		return errors.New("header must use Name: value")
	}
	if *headers == nil {
		*headers = make(headerFlags)
	}
	http.Header(*headers).Add(name, value)
	return nil
}

func runProxyCommand(ctx context.Context, args []string, stdout, stderr io.Writer) error {
	if len(args) == 0 || strings.HasPrefix(args[0], "-") {
		return runProxy(ctx, args, stdout, stderr)
	}
	switch args[0] {
	case "status":
		return runProxyStatus(ctx, args[1:], stdout, stderr)
	case "transactions", "history":
		return runProxyTransactions(ctx, args[1:], stdout, stderr)
	case "transaction":
		return runProxyTransaction(ctx, args[1:], stdout, stderr)
	case "stats":
		return runProxyStats(ctx, args[1:], stdout, stderr)
	case "clear":
		return runProxyClear(ctx, args[1:], stdout, stderr)
	case "ca":
		return runProxyCA(ctx, args[1:], stdout, stderr)
	case "repeat", "repeater":
		return runProxyRepeat(ctx, args[1:], stdout, stderr)
	default:
		return fmt.Errorf("unknown proxy command %q", args[0])
	}
}

func runProxyStatus(ctx context.Context, args []string, stdout, stderr io.Writer) error {
	flags, options := newProxyAPIFlags("owtf proxy status", stderr, 30*time.Second)
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("proxy status accepts no positional arguments")
	}
	client, err := newProxyAPIClient(options, stdout)
	if err != nil {
		return err
	}
	return client.writeJSON(ctx, http.MethodGet, "/api/v2/health", nil)
}

func runProxyTransactions(ctx context.Context, args []string, stdout, stderr io.Writer) error {
	flags, options := newProxyAPIFlags("owtf proxy transactions", stderr, 30*time.Second)
	method := flags.String("method", "", "filter by HTTP method")
	status := flags.Int("status", 0, "filter by response status")
	urlText := flags.String("url", "", "filter by URL substring")
	search := flags.String("search", "", "search URL, headers, and bodies")
	offset := flags.Int("offset", 0, "number of matches to skip")
	limit := flags.Int("limit", 100, "maximum matches to return")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("proxy transactions accepts no positional arguments")
	}
	client, err := newProxyAPIClient(options, stdout)
	if err != nil {
		return err
	}
	values := make(url.Values)
	for name, value := range map[string]string{
		"method": *method, "url": *urlText, "search": *search,
	} {
		if value != "" {
			values.Set(name, value)
		}
	}
	if *status != 0 {
		values.Set("status", strconv.Itoa(*status))
	}
	values.Set("offset", strconv.Itoa(*offset))
	values.Set("limit", strconv.Itoa(*limit))
	return client.writeJSON(ctx, http.MethodGet, "/api/v2/transactions?"+values.Encode(), nil)
}

func runProxyTransaction(ctx context.Context, args []string, stdout, stderr io.Writer) error {
	flags, options := newProxyAPIFlags("owtf proxy transaction", stderr, 30*time.Second)
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 1 {
		return errors.New("proxy transaction requires one transaction ID")
	}
	id, err := strconv.ParseUint(flags.Arg(0), 10, 64)
	if err != nil || id == 0 {
		return errors.New("proxy transaction ID must be a positive integer")
	}
	client, err := newProxyAPIClient(options, stdout)
	if err != nil {
		return err
	}
	return client.writeJSON(ctx, http.MethodGet, "/api/v2/transactions/"+strconv.FormatUint(id, 10), nil)
}

func runProxyStats(ctx context.Context, args []string, stdout, stderr io.Writer) error {
	flags, options := newProxyAPIFlags("owtf proxy stats", stderr, 30*time.Second)
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("proxy stats accepts no positional arguments")
	}
	client, err := newProxyAPIClient(options, stdout)
	if err != nil {
		return err
	}
	return client.writeJSON(ctx, http.MethodGet, "/api/v2/transactions/stats", nil)
}

func runProxyClear(ctx context.Context, args []string, stdout, stderr io.Writer) error {
	flags, options := newProxyAPIFlags("owtf proxy clear", stderr, 30*time.Second)
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("proxy clear accepts no positional arguments")
	}
	client, err := newProxyAPIClient(options, stdout)
	if err != nil {
		return err
	}
	return client.writeJSON(ctx, http.MethodDelete, "/api/v2/transactions", nil)
}

func runProxyCA(ctx context.Context, args []string, stdout, stderr io.Writer) error {
	flags, options := newProxyAPIFlags("owtf proxy ca", stderr, 30*time.Second)
	output := flags.String("output", "owtf-proxy-ca.crt", "CA certificate output path")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("proxy ca accepts no positional arguments")
	}
	client, err := newProxyAPIClient(options, stdout)
	if err != nil {
		return err
	}
	response, err := client.do(ctx, http.MethodGet, "/api/v2/ca", nil)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	written, err := writeProxyFile(*output, response.Body, 0o644)
	if err != nil {
		return err
	}
	return json.NewEncoder(stdout).Encode(map[string]any{"output": *output, "bytes": written})
}

func runProxyRepeat(ctx context.Context, args []string, stdout, stderr io.Writer) error {
	flags, options := newProxyAPIFlags("owtf proxy repeat", stderr, 2*time.Minute)
	method := flags.String("method", http.MethodGet, "HTTP method")
	data := flags.String("data", "", "request body text")
	dataFile := flags.String("data-file", "", "request body file")
	output := flags.String("output", "", "optional response body output path")
	var headers headerFlags
	flags.Var(&headers, "header", "request header in Name: value form; repeat for multiple values")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 1 {
		return errors.New("proxy repeat requires one absolute HTTP URL")
	}
	if *data != "" && *dataFile != "" {
		return errors.New("proxy repeat accepts only one of --data or --data-file")
	}
	body := []byte(*data)
	if *dataFile != "" {
		var err error
		body, err = readProxyDataFile(*dataFile)
		if err != nil {
			return err
		}
	}
	client, err := newProxyAPIClient(options, stdout)
	if err != nil {
		return err
	}
	input := owtfproxy.RepeatRequest{
		Method: *method, URL: flags.Arg(0), Headers: http.Header(headers),
		BodyBase64: base64.StdEncoding.EncodeToString(body),
	}
	var result owtfproxy.RepeatResponse
	if err := client.requestJSON(ctx, http.MethodPost, "/api/v2/repeater", input, &result); err != nil {
		return err
	}
	if *output != "" {
		body, err := base64.StdEncoding.DecodeString(result.BodyBase64)
		if err != nil {
			return fmt.Errorf("decode repeated response: %w", err)
		}
		if _, err := writeProxyFile(*output, bytes.NewReader(body), 0o600); err != nil {
			return err
		}
	}
	return writeIndentedJSON(stdout, result)
}

func newProxyAPIFlags(name string, stderr io.Writer, timeout time.Duration) (*flag.FlagSet, *proxyAPIOptions) {
	flags := flag.NewFlagSet(name, flag.ContinueOnError)
	flags.SetOutput(stderr)
	options := new(proxyAPIOptions)
	options.bind(flags, timeout)
	return flags, options
}

func newProxyAPIClient(options *proxyAPIOptions, output io.Writer) (*proxyAPIClient, error) {
	if options.timeout <= 0 {
		return nil, errors.New("proxy API timeout must be positive")
	}
	parsed, err := url.Parse(options.address)
	if err != nil || (parsed.Scheme != "http" && parsed.Scheme != "https") || parsed.Host == "" {
		return nil, fmt.Errorf("invalid proxy API URL %q", options.address)
	}
	parsed.Path = strings.TrimRight(parsed.Path, "/")
	return &proxyAPIClient{
		baseURL: parsed, client: &http.Client{Timeout: options.timeout}, output: output,
	}, nil
}

func (client *proxyAPIClient) writeJSON(ctx context.Context, method, path string, body any) error {
	var value any
	if err := client.requestJSON(ctx, method, path, body, &value); err != nil {
		return err
	}
	return writeIndentedJSON(client.output, value)
}

func (client *proxyAPIClient) requestJSON(ctx context.Context, method, path string, body, destination any) error {
	response, err := client.do(ctx, method, path, body)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	decoder := json.NewDecoder(io.LimitReader(response.Body, 32<<20))
	if err := decoder.Decode(destination); err != nil {
		return fmt.Errorf("decode proxy API response: %w", err)
	}
	return nil
}

func (client *proxyAPIClient) do(ctx context.Context, method, path string, body any) (*http.Response, error) {
	var source io.Reader
	if body != nil {
		data, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		source = bytes.NewReader(data)
	}
	endpoint := *client.baseURL
	endpoint.Path = strings.TrimRight(client.baseURL.Path, "/") + path
	endpoint.RawQuery = ""
	if index := strings.IndexByte(path, '?'); index >= 0 {
		endpoint.Path = strings.TrimRight(client.baseURL.Path, "/") + path[:index]
		endpoint.RawQuery = path[index+1:]
	}
	request, err := http.NewRequestWithContext(ctx, method, endpoint.String(), source)
	if err != nil {
		return nil, err
	}
	request.Header.Set("Accept", "application/json")
	if body != nil {
		request.Header.Set("Content-Type", "application/json")
	}
	response, err := client.client.Do(request)
	if err != nil {
		return nil, fmt.Errorf("%s %s: %w", method, endpoint.String(), err)
	}
	if response.StatusCode >= 200 && response.StatusCode < 300 {
		return response, nil
	}
	defer response.Body.Close()
	data, _ := io.ReadAll(io.LimitReader(response.Body, 1<<20))
	var serverError struct {
		Error string `json:"error"`
	}
	if json.Unmarshal(data, &serverError) == nil && serverError.Error != "" {
		return nil, fmt.Errorf("%s %s: %s", method, path, serverError.Error)
	}
	return nil, fmt.Errorf("%s %s: server returned %s", method, path, response.Status)
}

func readProxyDataFile(path string) ([]byte, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open repeater data: %w", err)
	}
	defer file.Close()
	data, err := io.ReadAll(io.LimitReader(file, maximumCLIDataFile+1))
	if err != nil {
		return nil, fmt.Errorf("read repeater data: %w", err)
	}
	if len(data) > maximumCLIDataFile {
		return nil, fmt.Errorf("repeater data file exceeds %d bytes", maximumCLIDataFile)
	}
	return data, nil
}

func writeProxyFile(path string, source io.Reader, mode os.FileMode) (int64, error) {
	directory := filepath.Dir(path)
	if err := os.MkdirAll(directory, 0o750); err != nil {
		return 0, fmt.Errorf("create output directory: %w", err)
	}
	file, err := os.CreateTemp(directory, ".owtf-proxy-*")
	if err != nil {
		return 0, fmt.Errorf("create output file: %w", err)
	}
	temporary := file.Name()
	defer os.Remove(temporary)
	if err := file.Chmod(mode); err != nil {
		file.Close()
		return 0, err
	}
	written, copyErr := io.Copy(file, source)
	closeErr := file.Close()
	if copyErr != nil {
		return written, fmt.Errorf("write output file: %w", copyErr)
	}
	if closeErr != nil {
		return written, fmt.Errorf("close output file: %w", closeErr)
	}
	if err := os.Rename(temporary, path); err != nil {
		return written, fmt.Errorf("publish output file: %w", err)
	}
	return written, nil
}

func writeIndentedJSON(output io.Writer, value any) error {
	encoder := json.NewEncoder(output)
	encoder.SetIndent("", "  ")
	return encoder.Encode(value)
}
