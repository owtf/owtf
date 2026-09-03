package plugin

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

const maxCapturedBody = 1 << 20

// HTTPCollector returns the baseline HTTP evidence collector. Redirects remain
// on the original host and response bodies are retained with a bounded size.
func HTTPCollector(client *http.Client) Executor {
	if client == nil {
		client = &http.Client{Timeout: 20 * time.Second}
	}
	return func(ctx context.Context, request Request) (Result, error) {
		if request.Target.Kind != "url" {
			return Result{}, fmt.Errorf("HTTP collector requires a URL target")
		}
		targetURL, err := url.Parse(request.Target.Value)
		if err != nil {
			return Result{}, fmt.Errorf("parse target URL: %w", err)
		}

		collectorClient := *client
		collectorClient.CheckRedirect = func(req *http.Request, via []*http.Request) error {
			if !strings.EqualFold(req.URL.Host, targetURL.Host) {
				return http.ErrUseLastResponse
			}
			if len(via) >= 10 {
				return fmt.Errorf("stopped after 10 redirects")
			}
			return nil
		}

		req, err := http.NewRequestWithContext(ctx, http.MethodGet, targetURL.String(), nil)
		if err != nil {
			return Result{}, fmt.Errorf("create request: %w", err)
		}
		req.Header.Set("User-Agent", "OWTF/0.1")
		request.Log("system", "fetching "+targetURL.Redacted())
		started := time.Now()
		response, err := collectorClient.Do(req)
		if err != nil {
			return Result{}, fmt.Errorf("fetch target: %w", err)
		}
		defer response.Body.Close()
		body, err := io.ReadAll(io.LimitReader(response.Body, maxCapturedBody+1))
		if err != nil {
			return Result{}, fmt.Errorf("read response: %w", err)
		}
		truncated := len(body) > maxCapturedBody
		if truncated {
			body = body[:maxCapturedBody]
			request.Log("system", "response body truncated at 1 MiB")
		}

		requestHeaders, _ := json.Marshal(req.Header)
		responseHeaders, _ := json.Marshal(response.Header)
		observation, _ := json.Marshal(map[string]any{
			"status_code":  response.StatusCode,
			"content_type": response.Header.Get("Content-Type"),
			"server":       response.Header.Get("Server"),
			"truncated":    truncated,
		})
		request.Log("stdout", fmt.Sprintf("%s %s", response.Proto, response.Status))

		return Result{
			Artifacts: []ArtifactResult{{
				Name: "response-body", MediaType: response.Header.Get("Content-Type"), Data: body,
			}},
			Transactions: []TransactionResult{{
				Method:                   http.MethodGet,
				URL:                      targetURL.String(),
				RequestHeaders:           string(requestHeaders),
				StatusCode:               response.StatusCode,
				ResponseHeaders:          string(responseHeaders),
				ResponseBodyArtifactName: "response-body",
				DurationMS:               time.Since(started).Milliseconds(),
			}},
			Observations: []ObservationResult{{
				TechniqueCode: "OWTF-WSP-001", Kind: "http.response", Data: string(observation),
			}},
		}, nil
	}
}
