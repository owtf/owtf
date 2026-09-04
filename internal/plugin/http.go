package plugin

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/owtf/owtf/internal/model"
)

const (
	maxCapturedBody   = 1 << 20
	maxDiscoveredURLs = 1000
)

// HTTPExecutor performs the read-only requests declared by an HTTP plugin.
// Redirects cannot leave the target host and response bodies are bounded.
func HTTPExecutor(manifest Manifest, client *http.Client, userAgent string) Executor {
	spec := *manifest.Spec.Runtime.HTTP
	spec.Probes = append([]HTTPProbe(nil), spec.Probes...)
	targetKinds := append([]string(nil), manifest.Spec.TargetKinds...)
	techniqueCode := manifest.Spec.Techniques[0].Code
	if userAgent == "" {
		userAgent = "OWTF/0.1"
	}
	if client == nil {
		client = &http.Client{Timeout: 20 * time.Second}
	}

	return func(ctx context.Context, request Request) (Result, error) {
		if !supportsTarget(targetKinds, request.Target.Kind) {
			return Result{}, fmt.Errorf("plugin does not support %s targets", request.Target.Kind)
		}
		targetURL, err := url.Parse(request.Target.Value)
		if err != nil || targetURL.Host == "" || (targetURL.Scheme != "http" && targetURL.Scheme != "https") {
			return Result{}, fmt.Errorf("HTTP plugin requires an HTTP or HTTPS URL target")
		}

		httpClient := *client
		httpClient.CheckRedirect = sameHostRedirects(targetURL)
		result := Result{}
		for _, probe := range spec.Probes {
			probeURL, err := resolveProbeURL(targetURL, probe.Path)
			if err != nil {
				return Result{}, fmt.Errorf("resolve HTTP probe %q: %w", probe.Name, err)
			}
			request.Log("system", fmt.Sprintf("%s %s", probe.Method, probeURL.Redacted()))
			started := time.Now()
			httpRequest, err := http.NewRequestWithContext(ctx, probe.Method, probeURL.String(), nil)
			if err != nil {
				return Result{}, fmt.Errorf("create HTTP probe %q: %w", probe.Name, err)
			}
			httpRequest.Header.Set("User-Agent", userAgent)
			response, err := httpClient.Do(httpRequest)
			if err != nil {
				return Result{}, fmt.Errorf("run HTTP probe %q: %w", probe.Name, err)
			}
			body, truncated, err := readHTTPBody(response.Body)
			response.Body.Close()
			if err != nil {
				return Result{}, fmt.Errorf("read HTTP probe %q response: %w", probe.Name, err)
			}
			if truncated {
				request.Log("system", fmt.Sprintf("%s response body truncated at 1 MiB", probe.Name))
			}

			artifactName := ""
			if len(body) != 0 {
				artifactName = probe.Name
				result.Artifacts = append(result.Artifacts, ArtifactResult{
					Name: probe.Name, MediaType: response.Header.Get("Content-Type"), Data: body,
				})
			}
			requestHeaders, _ := json.Marshal(httpRequest.Header)
			responseHeaders, _ := json.Marshal(response.Header)
			result.Transactions = append(result.Transactions, TransactionResult{
				Method: probe.Method, URL: probeURL.String(), RequestHeaders: string(requestHeaders),
				StatusCode: response.StatusCode, ResponseHeaders: string(responseHeaders),
				ResponseBodyArtifactName: artifactName, DurationMS: time.Since(started).Milliseconds(),
			})

			discovered := []URLResult{}
			if probe.Discover == "robots" && response.StatusCode >= 200 && response.StatusCode < 300 {
				discovered = discoverRobotsURLs(targetURL, body)
				result.URLs = append(result.URLs, discovered...)
			}
			observation, _ := json.Marshal(map[string]any{
				"name": probe.Name, "method": probe.Method, "url": probeURL.String(),
				"status_code": response.StatusCode, "content_type": response.Header.Get("Content-Type"),
				"server": response.Header.Get("Server"), "allow": response.Header.Get("Allow"),
				"truncated": truncated, "discovered_urls": len(discovered),
			})
			result.Observations = append(result.Observations, ObservationResult{
				TechniqueCode: techniqueCode, Kind: model.ObservationKindHTTPResponse, Data: string(observation),
			})
			request.Log("stdout", fmt.Sprintf("%s %s", response.Proto, response.Status))
		}
		return result, nil
	}
}

func sameHostRedirects(target *url.URL) func(*http.Request, []*http.Request) error {
	return func(request *http.Request, via []*http.Request) error {
		if !strings.EqualFold(request.URL.Host, target.Host) {
			return http.ErrUseLastResponse
		}
		if len(via) >= 10 {
			return fmt.Errorf("stopped after 10 redirects")
		}
		return nil
	}
}

func resolveProbeURL(target *url.URL, path string) (*url.URL, error) {
	if path == "" {
		copy := *target
		return &copy, nil
	}
	reference, err := url.Parse(path)
	if err != nil {
		return nil, err
	}
	return target.ResolveReference(reference), nil
}

func readHTTPBody(body io.Reader) ([]byte, bool, error) {
	data, err := io.ReadAll(io.LimitReader(body, maxCapturedBody+1))
	if err != nil {
		return nil, false, err
	}
	if len(data) <= maxCapturedBody {
		return data, false, nil
	}
	return data[:maxCapturedBody], true, nil
}

func discoverRobotsURLs(origin *url.URL, body []byte) []URLResult {
	seen := make(map[string]bool)
	result := make([]URLResult, 0)
	for _, rawLine := range bytes.Split(body, []byte{'\n'}) {
		line := strings.TrimSpace(strings.TrimSuffix(string(rawLine), "\r"))
		if comment := strings.IndexByte(line, '#'); comment >= 0 {
			line = strings.TrimSpace(line[:comment])
		}
		key, value, found := strings.Cut(line, ":")
		if !found {
			continue
		}
		key = strings.ToLower(strings.TrimSpace(key))
		value = strings.TrimSpace(value)
		if value == "" || key != "sitemap" && key != "allow" && key != "disallow" {
			continue
		}
		if key != "sitemap" && (!strings.HasPrefix(value, "/") || strings.ContainsAny(value, "*$")) {
			continue
		}
		reference, err := url.Parse(value)
		if err != nil || reference.User != nil {
			continue
		}
		candidate := origin.ResolveReference(reference)
		candidate.Fragment = ""
		if candidate.Host == "" || candidate.Scheme != "http" && candidate.Scheme != "https" {
			continue
		}
		value = candidate.String()
		if seen[value] {
			continue
		}
		seen[value] = true
		result = append(result, URLResult{URL: value})
		if len(result) == maxDiscoveredURLs {
			break
		}
	}
	return result
}
