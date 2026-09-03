package main

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
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
	if err != nil || repeatResponse.StatusCode != http.StatusOK || repeated.StatusCode != http.StatusAccepted || string(repeatedBody) != "modified" {
		cancel()
		t.Fatalf("repeater HTTP status = %d, response = %+v, body = %q, error = %v", repeatResponse.StatusCode, repeated, repeatedBody, err)
	}
	apiURL := "http://" + status.API
	var cliOutput bytes.Buffer
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
	if err != nil || cliRepeated.StatusCode != http.StatusAccepted || string(cliBody) != "modified" {
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
	if statsResponse.StatusCode != http.StatusOK || stats.Total != 3 {
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
	if len(transactions) != 3 || transactions[0].URL != upstream.URL+"/through-proxy" ||
		transactions[1].URL != upstream.URL+"/repeat" || transactions[2].URL != upstream.URL+"/cli-repeat" ||
		transactions[0].StatusCode != http.StatusAccepted || string(transactions[0].ResponseBody) != "modified" ||
		string(transactions[1].ResponseBody) != "modified" || string(transactions[2].ResponseBody) != "modified" {
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
