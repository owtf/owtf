package main

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/owtf/owtf/internal/har"
	owtfproxy "github.com/owtf/owtf/internal/proxy"
)

func TestRunProxyCapturesTrafficAndStopsCleanly(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.Header.Get("X-OWTF") != "intercepted" {
			http.Error(writer, "request was not intercepted", http.StatusInternalServerError)
			return
		}
		writer.WriteHeader(http.StatusAccepted)
		_, _ = writer.Write([]byte("captured"))
	}))
	defer upstream.Close()

	directory := t.TempDir()
	outputPath := filepath.Join(directory, "capture.har")
	certificatePath := filepath.Join(directory, "ca.crt")
	keyPath := filepath.Join(directory, "ca.key")
	interceptorPath := filepath.Join(directory, "interceptors.json")
	if err := os.WriteFile(interceptorPath, []byte(`{"rules":[
		{"name":"request","phase":"request","action":{"set_headers":{"X-OWTF":"intercepted"}}},
		{"name":"response","phase":"response","action":{"body_replace":[{"pattern":"captured","replacement":"modified"}]}}
	]}`), 0o600); err != nil {
		t.Fatal(err)
	}
	outputReader, outputWriter := io.Pipe()
	defer outputReader.Close()

	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() {
		done <- runProxy(ctx, []string{
			"--listen", "127.0.0.1:0",
			"--api-listen", "127.0.0.1:0",
			"--output", outputPath,
			"--ca-cert", certificatePath,
			"--ca-key", keyPath,
			"--interceptor-file", interceptorPath,
		}, outputWriter, io.Discard)
		_ = outputWriter.Close()
	}()

	var status struct {
		Listen string `json:"listen"`
		API    string `json:"api"`
	}
	if err := json.NewDecoder(outputReader).Decode(&status); err != nil {
		cancel()
		t.Fatal(err)
	}
	proxyURL, err := url.Parse("http://" + status.Listen)
	if err != nil {
		cancel()
		t.Fatal(err)
	}
	client := &http.Client{
		Timeout:   2 * time.Second,
		Transport: &http.Transport{Proxy: http.ProxyURL(proxyURL)},
	}
	response, err := client.Get(upstream.URL + "/through-proxy")
	if err != nil {
		cancel()
		t.Fatal(err)
	}
	body, _ := io.ReadAll(response.Body)
	response.Body.Close()
	if response.StatusCode != http.StatusAccepted || string(body) != "modified" {
		cancel()
		t.Fatalf("status = %d, body = %q", response.StatusCode, body)
	}
	apiURL := "http://" + status.API
	var cliOutput bytes.Buffer
	if err := runProxyCommand(context.Background(), []string{
		"interceptors", "list", "--api", apiURL,
	}, &cliOutput, io.Discard); err != nil {
		cancel()
		t.Fatal(err)
	}
	var interceptorConfig owtfproxy.InterceptorConfig
	if err := json.Unmarshal(cliOutput.Bytes(), &interceptorConfig); err != nil || len(interceptorConfig.Rules) != 2 {
		cancel()
		t.Fatalf("CLI interceptors = %+v, error = %v", interceptorConfig, err)
	}
	cliOutput.Reset()
	if err := runProxyCommand(context.Background(), []string{
		"interceptors", "disable", "--api", apiURL, "response",
	}, &cliOutput, io.Discard); err != nil {
		cancel()
		t.Fatal(err)
	}
	response, err = client.Get(upstream.URL + "/disabled")
	if err != nil {
		cancel()
		t.Fatal(err)
	}
	body, _ = io.ReadAll(response.Body)
	response.Body.Close()
	if response.StatusCode != http.StatusAccepted || string(body) != "captured" {
		cancel()
		t.Fatalf("disabled interceptor status = %d, body = %q", response.StatusCode, body)
	}
	cliOutput.Reset()
	if err := runProxyCommand(context.Background(), []string{
		"interceptors", "enable", "--api", apiURL, "response",
	}, &cliOutput, io.Discard); err != nil {
		cancel()
		t.Fatal(err)
	}
	runtimeInterceptorPath := filepath.Join(directory, "runtime-interceptors.json")
	if err := os.WriteFile(runtimeInterceptorPath, []byte(`{"rules":[
		{"name":"request","phase":"request","action":{"set_headers":{"X-OWTF":"intercepted"}}},
		{"name":"response","phase":"response","action":{"body_replace":[{"pattern":"captured","replacement":"runtime"}]}}
	]}`), 0o600); err != nil {
		cancel()
		t.Fatal(err)
	}
	cliOutput.Reset()
	if err := runProxyCommand(context.Background(), []string{
		"interceptors", "replace", "--api", apiURL, runtimeInterceptorPath,
	}, &cliOutput, io.Discard); err != nil {
		cancel()
		t.Fatal(err)
	}
	if err := json.Unmarshal(cliOutput.Bytes(), &interceptorConfig); err != nil || len(interceptorConfig.Rules) != 2 {
		cancel()
		t.Fatalf("CLI replacement = %+v, error = %v", interceptorConfig, err)
	}
	cliOutput.Reset()
	if err := runProxyCommand(context.Background(), []string{
		"intercept", "enable", "--api", apiURL, "--phase", "request", "--wait", "2s",
	}, &cliOutput, io.Discard); err != nil {
		cancel()
		t.Fatal(err)
	}
	liveDone := make(chan error, 1)
	go func() {
		response, err := client.Get(upstream.URL + "/live-before")
		if err == nil {
			body, readErr := io.ReadAll(response.Body)
			response.Body.Close()
			if readErr != nil {
				err = readErr
			} else if response.StatusCode != http.StatusAccepted || string(body) != "runtime" {
				err = fmt.Errorf("live CLI response status=%d body=%q", response.StatusCode, body)
			}
		}
		liveDone <- err
	}()
	var pending []owtfproxy.PendingInterception
	deadline := time.Now().Add(time.Second)
	for len(pending) == 0 && time.Now().Before(deadline) {
		cliOutput.Reset()
		if err := runProxyCommand(context.Background(), []string{
			"intercept", "list", "--api", apiURL,
		}, &cliOutput, io.Discard); err != nil {
			cancel()
			t.Fatal(err)
		}
		if err := json.Unmarshal(cliOutput.Bytes(), &pending); err != nil {
			cancel()
			t.Fatal(err)
		}
		if len(pending) == 0 {
			time.Sleep(time.Millisecond)
		}
	}
	if len(pending) != 1 {
		cancel()
		t.Fatalf("CLI pending interceptions = %+v", pending)
	}
	liveUpdatePath := filepath.Join(directory, "live-update.json")
	liveURL := upstream.URL + "/live-after"
	if err := os.WriteFile(liveUpdatePath, []byte(fmt.Sprintf(`{"url":%q}`, liveURL)), 0o600); err != nil {
		cancel()
		t.Fatal(err)
	}
	cliOutput.Reset()
	if err := runProxyCommand(context.Background(), []string{
		"intercept", "continue", "--api", apiURL, "--input", liveUpdatePath, pending[0].ID,
	}, &cliOutput, io.Discard); err != nil {
		cancel()
		t.Fatal(err)
	}
	if err := <-liveDone; err != nil {
		cancel()
		t.Fatal(err)
	}
	cliOutput.Reset()
	if err := runProxyCommand(context.Background(), []string{
		"intercept", "disable", "--api", apiURL,
	}, &cliOutput, io.Discard); err != nil {
		cancel()
		t.Fatal(err)
	}

	repeatInput, _ := json.Marshal(owtfproxy.RepeatRequest{Method: http.MethodGet, URL: upstream.URL + "/repeat"})
	repeatResponse, err := http.Post("http://"+status.API+"/api/v2/repeater", "application/json", bytes.NewReader(repeatInput))
	if err != nil {
		cancel()
		t.Fatal(err)
	}
	var repeated owtfproxy.RepeatResponse
	if err := json.NewDecoder(repeatResponse.Body).Decode(&repeated); err != nil {
		repeatResponse.Body.Close()
		cancel()
		t.Fatal(err)
	}
	repeatResponse.Body.Close()
	repeatedBody, err := base64.StdEncoding.DecodeString(repeated.BodyBase64)
	if err != nil || repeatResponse.StatusCode != http.StatusOK || repeated.StatusCode != http.StatusAccepted || string(repeatedBody) != "runtime" {
		cancel()
		t.Fatalf("repeater HTTP status = %d, response = %+v, body = %q, error = %v", repeatResponse.StatusCode, repeated, repeatedBody, err)
	}
	cliOutput.Reset()
	if err := runProxyCommand(context.Background(), []string{
		"repeat", "--api", apiURL, upstream.URL + "/cli-repeat",
	}, &cliOutput, io.Discard); err != nil {
		cancel()
		t.Fatal(err)
	}
	var cliRepeated owtfproxy.RepeatResponse
	if err := json.Unmarshal(cliOutput.Bytes(), &cliRepeated); err != nil {
		cancel()
		t.Fatal(err)
	}
	cliBody, err := base64.StdEncoding.DecodeString(cliRepeated.BodyBase64)
	if err != nil || cliRepeated.StatusCode != http.StatusAccepted || string(cliBody) != "runtime" {
		cancel()
		t.Fatalf("CLI repeat = %+v, body = %q, error = %v", cliRepeated, cliBody, err)
	}

	statsResponse, err := http.Get("http://" + status.API + "/api/v2/transactions/stats")
	if err != nil {
		cancel()
		t.Fatal(err)
	}
	var stats struct {
		Total int `json:"total"`
	}
	if err := json.NewDecoder(statsResponse.Body).Decode(&stats); err != nil {
		statsResponse.Body.Close()
		cancel()
		t.Fatal(err)
	}
	statsResponse.Body.Close()
	if statsResponse.StatusCode != http.StatusOK || stats.Total != 5 {
		cancel()
		t.Fatalf("proxy stats status = %d, stats = %+v", statsResponse.StatusCode, stats)
	}

	cliOutput.Reset()
	if err := runProxyCommand(context.Background(), []string{
		"transactions", "--api", apiURL, "--url", "/cli-repeat", "--limit", "1",
	}, &cliOutput, io.Discard); err != nil {
		cancel()
		t.Fatal(err)
	}
	var history []struct {
		ID  uint64 `json:"id"`
		URL string `json:"url"`
	}
	if err := json.Unmarshal(cliOutput.Bytes(), &history); err != nil || len(history) != 1 || history[0].URL != upstream.URL+"/cli-repeat" {
		cancel()
		t.Fatalf("CLI history = %+v, error = %v", history, err)
	}

	caOutput := filepath.Join(directory, "downloaded-ca.crt")
	cliOutput.Reset()
	if err := runProxyCommand(context.Background(), []string{
		"ca", "--api", apiURL, "--output", caOutput,
	}, &cliOutput, io.Discard); err != nil {
		cancel()
		t.Fatal(err)
	}
	generatedCA, _ := os.ReadFile(certificatePath)
	downloadedCA, _ := os.ReadFile(caOutput)
	if !bytes.Equal(generatedCA, downloadedCA) {
		cancel()
		t.Fatal("CLI downloaded a different proxy CA")
	}

	cancel()
	select {
	case err := <-done:
		if err != nil {
			t.Fatal(err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("proxy did not stop after cancellation")
	}

	file, err := os.Open(outputPath)
	if err != nil {
		t.Fatal(err)
	}
	transactions, parseErr := har.Parse(file)
	file.Close()
	if parseErr != nil {
		t.Fatal(parseErr)
	}
	if len(transactions) != 5 || transactions[0].URL != upstream.URL+"/through-proxy" ||
		transactions[1].URL != upstream.URL+"/disabled" || transactions[2].URL != liveURL ||
		transactions[3].URL != upstream.URL+"/repeat" || transactions[4].URL != upstream.URL+"/cli-repeat" ||
		transactions[0].StatusCode != http.StatusAccepted || string(transactions[0].ResponseBody) != "modified" ||
		string(transactions[1].ResponseBody) != "captured" || string(transactions[2].ResponseBody) != "runtime" ||
		string(transactions[3].ResponseBody) != "runtime" || string(transactions[4].ResponseBody) != "runtime" {
		t.Fatalf("transactions = %+v", transactions)
	}
}

func TestLoadHTTPCredentialsRequiresPrivateRegularFile(t *testing.T) {
	path := filepath.Join(t.TempDir(), "auth.json")
	if err := os.WriteFile(path, []byte(`{"example.test":{"username":"operator","password":"secret"}}`), 0o600); err != nil {
		t.Fatal(err)
	}
	credentials, err := loadHTTPCredentials(path)
	if err != nil {
		t.Fatal(err)
	}
	if credentials["example.test"].Username != "operator" {
		t.Fatalf("credentials = %+v", credentials)
	}
	if err := os.Chmod(path, 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := loadHTTPCredentials(path); err == nil {
		t.Fatal("public credential file was accepted")
	}
}

func TestProxyConfigurationPrecedence(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config.yaml")
	if err := os.WriteFile(path, []byte(`
apiVersion: owtf.dev/v1alpha1
kind: Config
proxy:
  attempts: 2
  cacheEntries: 0
  targetHosts: [file.example]
`), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("OWTF_PROXY_ATTEMPTS", "3")
	settings, err := proxyConfiguration([]string{
		"--config", path,
		"--attempts", "4",
		"--target-host", "flag.example",
	}, io.Discard)
	if err != nil {
		t.Fatal(err)
	}
	if settings.Proxy.Attempts != 4 || settings.Proxy.CacheEntries != 0 ||
		len(settings.Proxy.TargetHosts) != 1 || settings.Proxy.TargetHosts[0] != "flag.example" {
		t.Fatalf("proxy configuration = %+v", settings.Proxy)
	}
}
