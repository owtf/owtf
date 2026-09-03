package main

import (
	"context"
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
)

func TestRunProxyCapturesTrafficAndStopsCleanly(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		writer.WriteHeader(http.StatusAccepted)
		_, _ = writer.Write([]byte("captured"))
	}))
	defer upstream.Close()

	directory := t.TempDir()
	outputPath := filepath.Join(directory, "capture.har")
	certificatePath := filepath.Join(directory, "ca.crt")
	keyPath := filepath.Join(directory, "ca.key")
	outputReader, outputWriter := io.Pipe()
	defer outputReader.Close()

	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() {
		done <- runProxy(ctx, []string{
			"--listen", "127.0.0.1:0",
			"--output", outputPath,
			"--ca-cert", certificatePath,
			"--ca-key", keyPath,
		}, outputWriter, io.Discard)
		_ = outputWriter.Close()
	}()

	var status struct {
		Listen string `json:"listen"`
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
	_, _ = io.Copy(io.Discard, response.Body)
	response.Body.Close()
	if response.StatusCode != http.StatusAccepted {
		cancel()
		t.Fatalf("status = %d", response.StatusCode)
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
	if len(transactions) != 1 || transactions[0].URL != upstream.URL+"/through-proxy" || transactions[0].StatusCode != http.StatusAccepted {
		t.Fatalf("transactions = %+v", transactions)
	}
}
