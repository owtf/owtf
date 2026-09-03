package proxy

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"sort"
	"strings"
	"time"
)

const (
	maxInterceptorRules        = 100
	maxInterceptorReplacements = 10_000
)

// ErrInterceptorBodyTooLarge means a body-modifying rule exceeded its bound.
var ErrInterceptorBodyTooLarge = errors.New("interceptor body exceeds configured limit")

// InterceptorConfig is the persisted static interceptor configuration.
type InterceptorConfig struct {
	Rules []InterceptorRule `json:"rules"`
}

// InterceptorRule applies an action to matching request or response traffic.
// A nil Enabled value defaults to true.
type InterceptorRule struct {
	Name     string            `json:"name"`
	Enabled  *bool             `json:"enabled,omitempty"`
	Priority int               `json:"priority"`
	Phase    string            `json:"phase"`
	Match    InterceptorMatch  `json:"match,omitempty"`
	Action   InterceptorAction `json:"action"`
}

// InterceptorMatch limits a rule by URL, HTTP method, or content type.
type InterceptorMatch struct {
	URLPattern   string   `json:"url_pattern,omitempty"`
	Methods      []string `json:"methods,omitempty"`
	ContentTypes []string `json:"content_types,omitempty"`
}

// InterceptorAction describes supported request and response modifications.
type InterceptorAction struct {
	SetHeaders    map[string]string `json:"set_headers,omitempty"`
	AddHeaders    map[string]string `json:"add_headers,omitempty"`
	RemoveHeaders []string          `json:"remove_headers,omitempty"`
	BodyReplace   []TextReplacement `json:"body_replace,omitempty"`
	BodyPrepend   string            `json:"body_prepend,omitempty"`
	BodyAppend    string            `json:"body_append,omitempty"`
	RewriteURL    *TextReplacement  `json:"rewrite_url,omitempty"`
	DelayMS       int               `json:"delay_ms,omitempty"`
}

// TextReplacement is a compiled regular-expression substitution.
type TextReplacement struct {
	Pattern     string `json:"pattern"`
	Replacement string `json:"replacement"`
}

// Interceptors is an immutable, priority-ordered static rule set.
type Interceptors struct {
	rules       []compiledInterceptorRule
	maximumBody int64
}

type compiledInterceptorRule struct {
	rule        InterceptorRule
	urlPattern  *regexp.Regexp
	bodyReplace []compiledReplacement
	rewriteURL  *compiledReplacement
	methods     map[string]bool
}

type compiledReplacement struct {
	pattern     *regexp.Regexp
	replacement []byte
}

// LoadInterceptors decodes and validates one JSON rule document.
func LoadInterceptors(reader io.Reader, maximumBody int64) (*Interceptors, error) {
	data, err := io.ReadAll(io.LimitReader(reader, (1<<20)+1))
	if err != nil {
		return nil, fmt.Errorf("read interceptors: %w", err)
	}
	if len(data) > 1<<20 {
		return nil, errors.New("interceptor configuration exceeds 1 MiB")
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	var config InterceptorConfig
	if err := decoder.Decode(&config); err != nil {
		return nil, fmt.Errorf("decode interceptors: %w", err)
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		if err == nil {
			return nil, errors.New("decode interceptors: multiple JSON values")
		}
		return nil, fmt.Errorf("decode interceptors: %w", err)
	}
	return NewInterceptors(config.Rules, maximumBody)
}

// NewInterceptors validates and compiles static rules.
func NewInterceptors(rules []InterceptorRule, maximumBody int64) (*Interceptors, error) {
	if maximumBody < 1 {
		return nil, errors.New("interceptor maximum body must be positive")
	}
	if len(rules) > maxInterceptorRules {
		return nil, fmt.Errorf("interceptor rules exceed maximum %d", maxInterceptorRules)
	}
	compiled := make([]compiledInterceptorRule, 0, len(rules))
	names := make(map[string]bool, len(rules))
	for index, rule := range rules {
		if int64(len(rule.Action.BodyPrepend)) > maximumBody || int64(len(rule.Action.BodyAppend)) > maximumBody {
			return nil, fmt.Errorf("interceptor rule %d: body prefix or suffix exceeds maximum body", index+1)
		}
		item, err := compileInterceptorRule(rule)
		if err != nil {
			return nil, fmt.Errorf("interceptor rule %d: %w", index+1, err)
		}
		if names[item.rule.Name] {
			return nil, fmt.Errorf("interceptor rule %d: duplicate name %q", index+1, item.rule.Name)
		}
		names[item.rule.Name] = true
		compiled = append(compiled, item)
	}
	sort.SliceStable(compiled, func(left, right int) bool {
		return compiled[left].rule.Priority < compiled[right].rule.Priority
	})
	return &Interceptors{rules: compiled, maximumBody: maximumBody}, nil
}

// InterceptRequest applies all matching request rules.
func (i *Interceptors) InterceptRequest(ctx context.Context, request *http.Request) error {
	if i == nil {
		return nil
	}
	bodyLoaded := false
	bodyEncoded := encoded(request.Header)
	var body []byte
	for _, rule := range i.rules {
		if !rule.appliesTo("request") || !rule.matches(request, request.Header) {
			continue
		}
		if err := waitForInterceptor(ctx, rule.rule.Action.DelayMS); err != nil {
			return err
		}
		applyHeaders(request.Header, rule.rule.Action)
		if rule.rewriteURL != nil {
			data, err := replaceAllBounded([]byte(request.URL.String()), *rule.rewriteURL, 64<<10)
			if err != nil {
				return fmt.Errorf("interceptor %q URL rewrite: %w", rule.rule.Name, err)
			}
			value := string(data)
			rewritten, err := url.Parse(value)
			if err != nil || rewritten.Host == "" || (rewritten.Scheme != "http" && rewritten.Scheme != "https") {
				return fmt.Errorf("interceptor %q produced invalid URL %q", rule.rule.Name, value)
			}
			request.URL = rewritten
			request.Host = rewritten.Host
		}
		if rule.modifiesBody() {
			if bodyEncoded || encoded(request.Header) {
				return fmt.Errorf("interceptor %q cannot modify an encoded request body", rule.rule.Name)
			}
			if !bodyLoaded {
				var err error
				body, err = readInterceptorBody(request.Body, i.maximumBody)
				if err != nil {
					return fmt.Errorf("interceptor request body: %w", err)
				}
				bodyLoaded = true
			}
			modified, err := rule.modifyBody(body, i.maximumBody)
			if err != nil {
				return fmt.Errorf("interceptor %q request body: %w", rule.rule.Name, err)
			}
			body = modified
		}
	}
	if bodyLoaded {
		setRequestBody(request, body)
	}
	return nil
}

// InterceptResponse applies all matching response rules.
func (i *Interceptors) InterceptResponse(ctx context.Context, response *http.Response) error {
	if i == nil {
		return nil
	}
	bodyLoaded := false
	bodyEncoded := encoded(response.Header)
	var body []byte
	for _, rule := range i.rules {
		if !rule.appliesTo("response") || !rule.matches(response.Request, response.Header) {
			continue
		}
		if err := waitForInterceptor(ctx, rule.rule.Action.DelayMS); err != nil {
			return err
		}
		applyHeaders(response.Header, rule.rule.Action)
		if rule.modifiesBody() {
			if bodyEncoded || encoded(response.Header) {
				return fmt.Errorf("interceptor %q cannot modify an encoded response body", rule.rule.Name)
			}
			if !bodyLoaded {
				var err error
				body, err = readInterceptorBody(response.Body, i.maximumBody)
				if err != nil {
					return fmt.Errorf("interceptor response body: %w", err)
				}
				bodyLoaded = true
			}
			modified, err := rule.modifyBody(body, i.maximumBody)
			if err != nil {
				return fmt.Errorf("interceptor %q response body: %w", rule.rule.Name, err)
			}
			body = modified
		}
	}
	if bodyLoaded {
		response.Body = io.NopCloser(bytes.NewReader(body))
		response.ContentLength = int64(len(body))
		response.Header.Set("Content-Length", fmt.Sprint(len(body)))
		response.Header.Del("Content-MD5")
		response.Header.Del("ETag")
		response.TransferEncoding = nil
	}
	return nil
}

func compileInterceptorRule(rule InterceptorRule) (compiledInterceptorRule, error) {
	rule.Name = strings.TrimSpace(rule.Name)
	if rule.Name == "" || len(rule.Name) > 128 {
		return compiledInterceptorRule{}, errors.New("name must contain 1 to 128 characters")
	}
	rule.Phase = strings.ToLower(strings.TrimSpace(rule.Phase))
	if rule.Phase != "request" && rule.Phase != "response" && rule.Phase != "both" {
		return compiledInterceptorRule{}, fmt.Errorf("unsupported phase %q", rule.Phase)
	}
	if rule.Priority < -1000 || rule.Priority > 1000 {
		return compiledInterceptorRule{}, errors.New("priority must be between -1000 and 1000")
	}
	if rule.Action.DelayMS < 0 || rule.Action.DelayMS > 60_000 {
		return compiledInterceptorRule{}, errors.New("delay_ms must be between 0 and 60000")
	}
	if rule.Phase == "response" && rule.Action.RewriteURL != nil {
		return compiledInterceptorRule{}, errors.New("response rules cannot rewrite request URLs")
	}
	if err := validateHeaderActions(rule.Action); err != nil {
		return compiledInterceptorRule{}, err
	}
	if modifiesBodyAction(rule.Action) {
		for _, headers := range []map[string]string{rule.Action.SetHeaders, rule.Action.AddHeaders} {
			for name := range headers {
				if http.CanonicalHeaderKey(name) == "Content-Encoding" {
					return compiledInterceptorRule{}, errors.New("body rules cannot set Content-Encoding")
				}
			}
		}
	}
	compiled := compiledInterceptorRule{rule: rule, methods: make(map[string]bool)}
	if rule.Match.URLPattern != "" {
		pattern, err := compilePattern(rule.Match.URLPattern)
		if err != nil {
			return compiledInterceptorRule{}, fmt.Errorf("URL pattern: %w", err)
		}
		compiled.urlPattern = pattern
	}
	for _, method := range rule.Match.Methods {
		method = strings.ToUpper(strings.TrimSpace(method))
		if !validHeaderName(method) {
			return compiledInterceptorRule{}, fmt.Errorf("invalid HTTP method %q", method)
		}
		compiled.methods[method] = true
	}
	for _, contentType := range rule.Match.ContentTypes {
		if strings.TrimSpace(contentType) == "" {
			return compiledInterceptorRule{}, errors.New("content type match is empty")
		}
	}
	for _, replacement := range rule.Action.BodyReplace {
		item, err := compileReplacement(replacement)
		if err != nil {
			return compiledInterceptorRule{}, fmt.Errorf("body replacement: %w", err)
		}
		compiled.bodyReplace = append(compiled.bodyReplace, item)
	}
	if rule.Action.RewriteURL != nil {
		item, err := compileReplacement(*rule.Action.RewriteURL)
		if err != nil {
			return compiledInterceptorRule{}, fmt.Errorf("URL replacement: %w", err)
		}
		compiled.rewriteURL = &item
	}
	return compiled, nil
}

func compileReplacement(replacement TextReplacement) (compiledReplacement, error) {
	if len(replacement.Replacement) > 4096 {
		return compiledReplacement{}, errors.New("replacement exceeds 4096 bytes")
	}
	pattern, err := compilePattern(replacement.Pattern)
	if err != nil {
		return compiledReplacement{}, err
	}
	return compiledReplacement{pattern: pattern, replacement: []byte(replacement.Replacement)}, nil
}

func compilePattern(value string) (*regexp.Regexp, error) {
	if value == "" || len(value) > 4096 {
		return nil, errors.New("pattern must contain 1 to 4096 bytes")
	}
	pattern, err := regexp.Compile("(?i:" + value + ")")
	if err != nil {
		return nil, err
	}
	if pattern.MatchString("") {
		return nil, errors.New("pattern cannot match an empty string")
	}
	if pattern.NumSubexp() > 32 {
		return nil, errors.New("pattern cannot contain more than 32 capture groups")
	}
	return pattern, nil
}

func validateHeaderActions(action InterceptorAction) error {
	forbidden := map[string]bool{"Content-Length": true, "Host": true, "Trailer": true, "Transfer-Encoding": true}
	for _, headers := range []map[string]string{action.SetHeaders, action.AddHeaders} {
		for name, value := range headers {
			if !validHeaderName(name) || strings.ContainsAny(value, "\r\n") {
				return fmt.Errorf("invalid header %q", name)
			}
			if forbidden[http.CanonicalHeaderKey(name)] {
				return fmt.Errorf("interceptor cannot set framing header %q", name)
			}
		}
	}
	for _, name := range action.RemoveHeaders {
		if !validHeaderName(name) {
			return fmt.Errorf("invalid header %q", name)
		}
	}
	return nil
}

func validHeaderName(name string) bool {
	if name == "" {
		return false
	}
	for index := range len(name) {
		if !isAuthToken(name[index]) {
			return false
		}
	}
	return true
}

func (rule compiledInterceptorRule) appliesTo(phase string) bool {
	if rule.rule.Enabled != nil && !*rule.rule.Enabled {
		return false
	}
	return rule.rule.Phase == phase || rule.rule.Phase == "both"
}

func (rule compiledInterceptorRule) matches(request *http.Request, headers http.Header) bool {
	if request == nil || request.URL == nil {
		return false
	}
	if rule.urlPattern != nil && !rule.urlPattern.MatchString(request.URL.String()) {
		return false
	}
	if len(rule.methods) > 0 && !rule.methods[strings.ToUpper(request.Method)] {
		return false
	}
	if len(rule.rule.Match.ContentTypes) > 0 {
		contentType := strings.ToLower(headers.Get("Content-Type"))
		matched := false
		for _, candidate := range rule.rule.Match.ContentTypes {
			if strings.Contains(contentType, strings.ToLower(candidate)) {
				matched = true
				break
			}
		}
		if !matched {
			return false
		}
	}
	return true
}

func (rule compiledInterceptorRule) modifiesBody() bool {
	return modifiesBodyAction(rule.rule.Action)
}

func modifiesBodyAction(action InterceptorAction) bool {
	return len(action.BodyReplace) > 0 || action.BodyPrepend != "" || action.BodyAppend != ""
}

func (rule compiledInterceptorRule) modifyBody(body []byte, maximum int64) ([]byte, error) {
	var err error
	for _, replacement := range rule.bodyReplace {
		body, err = replaceAllBounded(body, replacement, maximum)
		if err != nil {
			return nil, err
		}
	}
	if rule.rule.Action.BodyPrepend != "" {
		if int64(len(body)+len(rule.rule.Action.BodyPrepend)) > maximum {
			return nil, ErrInterceptorBodyTooLarge
		}
		body = append([]byte(rule.rule.Action.BodyPrepend), body...)
	}
	if rule.rule.Action.BodyAppend != "" {
		if int64(len(body)+len(rule.rule.Action.BodyAppend)) > maximum {
			return nil, ErrInterceptorBodyTooLarge
		}
		body = append(body, rule.rule.Action.BodyAppend...)
	}
	return body, nil
}

func replaceAllBounded(source []byte, replacement compiledReplacement, maximum int64) ([]byte, error) {
	locations := replacement.pattern.FindAllSubmatchIndex(source, maxInterceptorReplacements+1)
	if len(locations) > maxInterceptorReplacements {
		return nil, errors.New("replacement exceeds match limit")
	}
	result := make([]byte, 0, len(source))
	offset := 0
	for _, location := range locations {
		start, end := location[0], location[1]
		if int64(len(result)+start-offset) > maximum {
			return nil, ErrInterceptorBodyTooLarge
		}
		result = append(result, source[offset:start]...)
		expanded := replacement.pattern.Expand(nil, replacement.replacement, source, location)
		if int64(len(result)+len(expanded)) > maximum {
			return nil, ErrInterceptorBodyTooLarge
		}
		result = append(result, expanded...)
		offset = end
	}
	if int64(len(result)+len(source)-offset) > maximum {
		return nil, ErrInterceptorBodyTooLarge
	}
	return append(result, source[offset:]...), nil
}

func applyHeaders(headers http.Header, action InterceptorAction) {
	for _, name := range action.RemoveHeaders {
		headers.Del(name)
	}
	for name, value := range action.SetHeaders {
		headers.Set(name, value)
	}
	for name, value := range action.AddHeaders {
		headers.Add(name, value)
	}
}

func readInterceptorBody(body io.ReadCloser, maximum int64) ([]byte, error) {
	if body == nil {
		return nil, nil
	}
	data, err := io.ReadAll(io.LimitReader(body, maximum+1))
	closeErr := body.Close()
	if err != nil {
		return nil, err
	}
	if closeErr != nil {
		return nil, closeErr
	}
	if int64(len(data)) > maximum {
		return nil, fmt.Errorf("%w: maximum is %d bytes", ErrInterceptorBodyTooLarge, maximum)
	}
	return data, nil
}

func setRequestBody(request *http.Request, body []byte) {
	copyBody := append([]byte(nil), body...)
	request.Body = io.NopCloser(bytes.NewReader(copyBody))
	request.GetBody = func() (io.ReadCloser, error) {
		return io.NopCloser(bytes.NewReader(copyBody)), nil
	}
	request.ContentLength = int64(len(copyBody))
	request.Header.Set("Content-Length", fmt.Sprint(len(copyBody)))
	request.TransferEncoding = nil
}

func encoded(headers http.Header) bool {
	encoding := strings.TrimSpace(headers.Get("Content-Encoding"))
	return encoding != "" && !strings.EqualFold(encoding, "identity")
}

func waitForInterceptor(ctx context.Context, milliseconds int) error {
	if milliseconds == 0 {
		return nil
	}
	timer := time.NewTimer(time.Duration(milliseconds) * time.Millisecond)
	defer timer.Stop()
	select {
	case <-timer.C:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}
