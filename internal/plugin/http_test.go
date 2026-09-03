package plugin

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"testing/fstest"

	"github.com/owtf/owtf/internal/model"
)

func TestHTTPExecutorCapturesProbesAndDiscoversRobotsURLs(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
		switch request.URL.Path {
		case "/robots.txt":
			response.Header().Set("Content-Type", "text/plain")
			response.Write([]byte("User-agent: *\nDisallow: /private\nAllow: /public\nDisallow: /wild/*\nSitemap: /sitemap.xml\n"))
		case "/entry":
			if request.Method != http.MethodOptions {
				t.Fatalf("method = %s, want OPTIONS", request.Method)
			}
			response.Header().Set("Allow", "GET, HEAD, OPTIONS")
			response.WriteHeader(http.StatusNoContent)
		default:
			http.NotFound(response, request)
		}
	}))
	defer server.Close()

	catalog, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(httpManifest(`
      probes:
        - name: robots-response
          method: get
          path: /robots.txt
          discover: robots
        - name: options-response
          method: OPTIONS
`))}})
	if err != nil {
		t.Fatal(err)
	}
	entry, ok := catalog.Get("OWTF-TEST-001-semi_passive")
	if !ok || entry.Availability != "ready" || entry.Executor == nil {
		t.Fatalf("HTTP plugin is not ready: %+v", entry)
	}

	result, err := HTTPExecutor(entry.Manifest, server.Client())(context.Background(), Request{
		Target: model.Target{Kind: "url", Value: server.URL + "/entry?source=test"},
		Log:    func(string, string) {},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Transactions) != 2 || result.Transactions[0].Method != http.MethodGet || result.Transactions[0].URL != server.URL+"/robots.txt" {
		t.Fatalf("unexpected transactions: %+v", result.Transactions)
	}
	if result.Transactions[1].Method != http.MethodOptions || result.Transactions[1].StatusCode != http.StatusNoContent || result.Transactions[1].ResponseBodyArtifactName != "" {
		t.Fatalf("unexpected OPTIONS transaction: %+v", result.Transactions[1])
	}
	if len(result.Artifacts) != 1 || result.Artifacts[0].Name != "robots-response" {
		t.Fatalf("unexpected artifacts: %+v", result.Artifacts)
	}
	wantURLs := []string{server.URL + "/private", server.URL + "/public", server.URL + "/sitemap.xml"}
	if len(result.URLs) != len(wantURLs) {
		t.Fatalf("discovered URLs = %+v, want %+v", result.URLs, wantURLs)
	}
	for index, want := range wantURLs {
		if result.URLs[index].URL != want || result.URLs[index].Visited {
			t.Fatalf("discovered URL[%d] = %+v, want %q unvisited", index, result.URLs[index], want)
		}
	}
	if len(result.Observations) != 2 || result.Observations[0].Kind != model.ObservationKindHTTPResponse {
		t.Fatalf("unexpected observations: %+v", result.Observations)
	}
	var observation map[string]any
	if err := json.Unmarshal([]byte(result.Observations[0].Data), &observation); err != nil {
		t.Fatal(err)
	}
	if observation["discovered_urls"] != float64(3) || observation["status_code"] != float64(http.StatusOK) {
		t.Fatalf("unexpected observation: %+v", observation)
	}
}

func TestHTTPExecutorDoesNotFollowCrossHostRedirects(t *testing.T) {
	var outsideRequests atomic.Int32
	outside := httptest.NewServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {
		outsideRequests.Add(1)
	}))
	defer outside.Close()
	origin := httptest.NewServer(http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
		http.Redirect(response, request, outside.URL, http.StatusFound)
	}))
	defer origin.Close()

	manifest := mustHTTPManifest(t, httpManifest(`
      probes:
        - name: redirect-response
          method: GET
`))
	result, err := HTTPExecutor(manifest, origin.Client())(context.Background(), Request{
		Target: model.Target{Kind: "url", Value: origin.URL}, Log: func(string, string) {},
	})
	if err != nil {
		t.Fatal(err)
	}
	if outsideRequests.Load() != 0 || len(result.Transactions) != 1 || result.Transactions[0].StatusCode != http.StatusFound {
		t.Fatalf("cross-host redirect escaped: requests=%d transactions=%+v", outsideRequests.Load(), result.Transactions)
	}
}

func TestHTTPExecutorBoundsResponseBodies(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(response http.ResponseWriter, _ *http.Request) {
		response.Write([]byte(strings.Repeat("x", maxCapturedBody+1)))
	}))
	defer server.Close()
	manifest := mustHTTPManifest(t, httpManifest(`
      probes:
        - name: bounded-response
          method: GET
`))
	result, err := HTTPExecutor(manifest, server.Client())(context.Background(), Request{
		Target: model.Target{Kind: "url", Value: server.URL}, Log: func(string, string) {},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Artifacts) != 1 || len(result.Artifacts[0].Data) != maxCapturedBody {
		t.Fatalf("artifact length = %d, want %d", len(result.Artifacts[0].Data), maxCapturedBody)
	}
	var observation map[string]any
	if err := json.Unmarshal([]byte(result.Observations[0].Data), &observation); err != nil {
		t.Fatal(err)
	}
	if observation["truncated"] != true {
		t.Fatalf("truncation was not reported: %+v", observation)
	}
}

func TestHTTPExecutorHonorsCancellation(t *testing.T) {
	started := make(chan struct{})
	server := httptest.NewServer(http.HandlerFunc(func(_ http.ResponseWriter, request *http.Request) {
		close(started)
		<-request.Context().Done()
	}))
	defer server.Close()
	manifest := mustHTTPManifest(t, httpManifest(`
      probes:
        - name: cancelled-response
          method: GET
`))
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() {
		_, err := HTTPExecutor(manifest, server.Client())(ctx, Request{
			Target: model.Target{Kind: "url", Value: server.URL}, Log: func(string, string) {},
		})
		done <- err
	}()
	<-started
	cancel()
	if err := <-done; !errors.Is(err, context.Canceled) {
		t.Fatalf("HTTP executor error = %v, want context cancellation", err)
	}
}

func TestHTTPManifestValidation(t *testing.T) {
	valid := httpManifest(`
      probes:
        - name: response
          method: GET
          path: /robots.txt
`)
	for name, manifest := range map[string]string{
		"missing probes": strings.Replace(valid, "      probes:\n        - name: response\n          method: GET\n          path: /robots.txt\n", "      probes: []\n", 1),
		"unsafe method":  strings.Replace(valid, "method: GET", "method: DELETE", 1),
		"remote path":    strings.Replace(valid, "path: /robots.txt", "path: https://other.test/robots.txt", 1),
		"fragment":       strings.Replace(valid, "path: /robots.txt", "path: /robots.txt#section", 1),
		"bad discovery":  strings.Replace(valid, "path: /robots.txt", "path: /robots.txt\n          discover: sitemap", 1),
		"wrong target":   strings.Replace(valid, "targetKinds: [url]", "targetKinds: [hostname]", 1),
		"requirements":   strings.Replace(valid, "  runtime:", "  requirements: {commands: [curl]}\n  runtime:", 1),
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(manifest)}}); err == nil {
				t.Fatal("invalid HTTP manifest was accepted")
			}
		})
	}
}

func mustHTTPManifest(t *testing.T, data string) Manifest {
	t.Helper()
	catalog, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(data)}})
	if err != nil {
		t.Fatal(err)
	}
	entry, _ := catalog.Get("OWTF-TEST-001-semi_passive")
	return entry.Manifest
}

func httpManifest(spec string) string {
	return `apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-TEST-001-semi_passive
  version: 0.1.0
  title: HTTP test
spec:
  techniques: [OWTF-TEST-001]
  group: web
  type: semi_passive
  targetKinds: [url]
  runtime:
    type: http
    http:` + spec
}
