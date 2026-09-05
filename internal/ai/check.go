package ai

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"charm.land/fantasy"
	"github.com/owtf/owtf/internal/config"
)

// CheckResult describes this check, not a certification of every model feature.
// Native schema enforcement, streaming, and security analysis are not tested.
type CheckResult struct {
	Alias         string `json:"alias"`
	Provider      string `json:"provider"`
	Model         string `json:"model"`
	SDK           string `json:"sdk"`
	ToolRoundTrip bool   `json:"tool_round_trip"`
	ValidatedJSON bool   `json:"validated_json"`
	DurationMS    int64  `json:"duration_ms"`
}

// Check sends a generated nonce, validates one echo tool call, then validates a
// JSON response containing a fresh tool-result nonce. It performs at most two
// HTTP requests, with one shared deadline, no retries, and no fallback model.
// The second nonce makes this a tool-result consumption check, not mere parroting.
func Check(ctx context.Context, settings config.AI, alias string) (CheckResult, error) {
	if err := settings.Validate(); err != nil {
		return CheckResult{}, err
	}
	if alias == "" {
		alias = settings.DefaultModel
	}
	m, ok := settings.Models[alias]
	if !ok {
		return CheckResult{}, errors.New("select a configured model alias with --model or ai.defaultModel")
	}
	p := settings.Providers[m.Provider]
	var key string
	if p.APIKeyEnv != "" {
		key = os.Getenv(p.APIKeyEnv)
		if strings.TrimSpace(key) == "" || strings.ContainsAny(key, "\r\n") {
			return CheckResult{}, errors.New("configured AI credential environment variable is missing or invalid")
		}
	}
	timeout := settings.TimeoutSeconds
	if timeout == 0 {
		timeout = 30
	}
	ctx, cancel := context.WithTimeout(ctx, time.Duration(timeout)*time.Second)
	defer cancel()
	started := time.Now()
	model, closeClient, err := newModel(ctx, p, m.Model, key)
	if err != nil {
		return CheckResult{}, errors.New("cannot initialize configured model provider")
	}
	defer closeClient()
	tokens := settings.MaxOutputTokens
	if tokens == 0 {
		tokens = 1024
	}
	nonce := randomNonce()
	choice := fantasy.ToolChoiceRequired
	call := fantasy.Call{
		Prompt: fantasy.Prompt{fantasy.NewUserMessage("Call echo_probe exactly once with nonce " + nonce +
			". After receiving the tool result, return only a JSON object with exactly one key, nonce," +
			" containing the NEW nonce from that result. No markdown.")},
		MaxOutputTokens: &tokens,
		ToolChoice:      &choice,
		Tools: []fantasy.Tool{fantasy.FunctionTool{
			Name:        "echo_probe",
			Description: "Harmless in-memory qualification probe. Returns a new nonce.",
			InputSchema: map[string]any{
				"type":                 "object",
				"properties":           map[string]any{"nonce": map[string]any{"type": "string"}},
				"required":             []string{"nonce"},
				"additionalProperties": false,
			},
		}},
	}
	response, err := generate(ctx, model, call)
	if err != nil {
		return CheckResult{}, err
	}
	calls := response.Content.ToolCalls()
	if len(calls) != 1 || calls[0].ToolName != "echo_probe" || calls[0].ToolCallID == "" || calls[0].Invalid || calls[0].ProviderExecuted {
		return CheckResult{}, errors.New("model check: expected exactly one client-side echo_probe call")
	}
	tc := calls[0]
	if !validNonce(tc.Input, nonce) {
		return CheckResult{}, errors.New("model check: invalid tool arguments")
	}
	nextNonce := randomNonce()
	result, _ := json.Marshal(map[string]string{"nonce": nextNonce})
	call.Prompt = append(call.Prompt,
		fantasy.Message{
			Role: fantasy.MessageRoleAssistant,
			Content: []fantasy.MessagePart{fantasy.ToolCallPart{
				ToolCallID: tc.ToolCallID, ToolName: tc.ToolName, Input: tc.Input,
				ProviderOptions: fantasy.ProviderOptions(tc.ProviderMetadata),
			}},
		},
		fantasy.Message{
			Role: fantasy.MessageRoleTool,
			Content: []fantasy.MessagePart{fantasy.ToolResultPart{
				ToolCallID: tc.ToolCallID,
				Output:     fantasy.ToolResultOutputContentText{Text: string(result)},
			}},
		},
	)
	choice = fantasy.ToolChoiceNone
	response, err = generate(ctx, model, call)
	if err != nil {
		return CheckResult{}, err
	}
	var output strings.Builder
	for _, part := range response.Content {
		if text, ok := fantasy.AsContentType[fantasy.TextContent](part); ok {
			output.WriteString(text.Text)
		}
	}
	if len(response.Content.ToolCalls()) != 0 || !validNonce(output.String(), nextNonce) {
		return CheckResult{}, errors.New("model check: expected a JSON object containing the tool-result nonce")
	}
	return CheckResult{
		Alias: alias, Provider: m.Provider, Model: m.Model,
		SDK:           "fantasy/" + fantasy.Version,
		ToolRoundTrip: true, ValidatedJSON: true,
		DurationMS: time.Since(started).Milliseconds(),
	}, nil
}

func generate(ctx context.Context, model fantasy.LanguageModel, call fantasy.Call) (response *fantasy.Response, err error) {
	// Fantasy's Gemini mapper currently dereferences absent usage metadata.
	// Keep third-party response-processing panics inside this narrow boundary;
	// never turn one into a successful or partially qualified result.
	defer func() {
		if recover() != nil {
			response = nil
			err = errors.New("model check: SDK could not process the provider response")
		}
	}()
	response, err = model.Generate(oneRequest(ctx), call)
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	if err != nil {
		// SDK errors can include raw prompts, credentials, and response bodies.
		// Preserve only our transport's sanitized failure classification.
		var failure *requestError
		if errors.As(err, &failure) {
			return nil, failure
		}
		return nil, errors.New("model request failed; verify endpoint, credentials, model, and provider availability")
	}
	if response == nil || response.FinishReason == fantasy.FinishReasonLength || response.FinishReason == fantasy.FinishReasonError || response.FinishReason == fantasy.FinishReasonContentFilter {
		return nil, errors.New("model check: incomplete or blocked response")
	}
	return response, nil
}

func randomNonce() string {
	var nonce [16]byte
	_, _ = rand.Read(nonce[:])
	return hex.EncodeToString(nonce[:])
}

// Token-level parsing also rejects duplicate keys, unlike unmarshalling a struct.
func validNonce(input, expected string) bool {
	d := json.NewDecoder(strings.NewReader(input))
	start, err := d.Token()
	if err != nil || start != json.Delim('{') {
		return false
	}
	key, err := d.Token()
	if err != nil || key != "nonce" {
		return false
	}
	var value string
	if d.Decode(&value) != nil || value != expected {
		return false
	}
	end, err := d.Token()
	if err != nil || end != json.Delim('}') {
		return false
	}
	_, err = d.Token()
	return err == io.EOF
}

type requestError struct {
	status int
	reason string
}

func (e *requestError) Error() string {
	if e.status != 0 {
		return fmt.Sprintf("model request failed: HTTP %d (not retried)", e.status)
	}
	return "model request failed: " + e.reason
}
