package proxy

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"mime"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

const (
	defaultHistoryLimit = 100
	maximumHistoryLimit = 1000
	maximumAPIJSON      = 2 << 20
)

type httpDoer interface {
	Do(*http.Request) (*http.Response, error)
}

// APIConfig defines the dependencies of the loopback proxy API.
type APIConfig struct {
	Authority    *Authority
	Recorder     *Recorder
	RepeatClient httpDoer
	Interceptors *Interceptors
	MaximumBody  int64
}

type apiServer struct {
	authority    *Authority
	recorder     *Recorder
	repeatClient httpDoer
	interceptors *Interceptors
	maximumBody  int64
}

// NewAPI returns the proxy history, CA, and repeater API.
func NewAPI(config APIConfig) (http.Handler, error) {
	if config.Authority == nil {
		return nil, errors.New("proxy API authority is required")
	}
	if config.Recorder == nil {
		return nil, errors.New("proxy API recorder is required")
	}
	if config.RepeatClient == nil {
		return nil, errors.New("proxy API repeat client is required")
	}
	if config.Interceptors == nil {
		return nil, errors.New("proxy API interceptors are required")
	}
	if config.MaximumBody < 1 {
		return nil, errors.New("proxy API maximum body must be positive")
	}
	server := &apiServer{
		authority: config.Authority, recorder: config.Recorder,
		repeatClient: config.RepeatClient, interceptors: config.Interceptors,
		maximumBody: config.MaximumBody,
	}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/v2/health", server.health)
	mux.HandleFunc("GET /api/v2/ca", server.ca)
	mux.HandleFunc("GET /api/v2/transactions", server.history)
	mux.HandleFunc("DELETE /api/v2/transactions", server.clear)
	mux.HandleFunc("GET /api/v2/transactions/stats", server.stats)
	mux.HandleFunc("GET /api/v2/transactions/{transactionID}", server.transaction)
	mux.HandleFunc("POST /api/v2/repeater", server.repeat)
	mux.HandleFunc("GET /api/v2/interceptors", server.listInterceptors)
	mux.HandleFunc("PUT /api/v2/interceptors", server.replaceInterceptors)
	mux.HandleFunc("PATCH /api/v2/interceptors", server.setInterceptorEnabled)
	return http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		writer.Header().Set("Cache-Control", "no-store")
		writer.Header().Set("X-Content-Type-Options", "nosniff")
		mux.ServeHTTP(writer, request)
	}), nil
}

func (c *apiServer) health(writer http.ResponseWriter, _ *http.Request) {
	writeAPIJSON(writer, http.StatusOK, map[string]string{"status": "ok"})
}

func (c *apiServer) ca(writer http.ResponseWriter, _ *http.Request) {
	writer.Header().Set("Content-Type", "application/x-pem-file")
	writer.Header().Set("Content-Disposition", `attachment; filename="owtf-proxy-ca.crt"`)
	writer.WriteHeader(http.StatusOK)
	_, _ = writer.Write(c.authority.CertificatePEM())
}

func (c *apiServer) history(writer http.ResponseWriter, request *http.Request) {
	filter, err := parseTransactionFilter(request.URL.Query())
	if err != nil {
		writeAPIError(writer, http.StatusBadRequest, err)
		return
	}
	captured := c.recorder.History(filter)
	result := make([]transactionSummary, len(captured))
	for index, transaction := range captured {
		result[index] = presentTransactionSummary(transaction)
	}
	writeAPIJSON(writer, http.StatusOK, result)
}

func (c *apiServer) transaction(writer http.ResponseWriter, request *http.Request) {
	id, err := strconv.ParseUint(request.PathValue("transactionID"), 10, 64)
	if err != nil || id == 0 {
		writeAPIError(writer, http.StatusBadRequest, errors.New("invalid transaction ID"))
		return
	}
	transaction, ok := c.recorder.Transaction(id)
	if !ok {
		writeAPIError(writer, http.StatusNotFound, errors.New("transaction not found"))
		return
	}
	writeAPIJSON(writer, http.StatusOK, presentTransaction(transaction))
}

func (c *apiServer) stats(writer http.ResponseWriter, _ *http.Request) {
	stats := c.recorder.Stats()
	writeAPIJSON(writer, http.StatusOK, transactionStats{
		Total: stats.Total, Methods: stats.Methods, Statuses: stats.Statuses,
	})
}

func (c *apiServer) clear(writer http.ResponseWriter, _ *http.Request) {
	writeAPIJSON(writer, http.StatusOK, map[string]int{"removed": c.recorder.Clear()})
}

func (c *apiServer) listInterceptors(writer http.ResponseWriter, _ *http.Request) {
	writeAPIJSON(writer, http.StatusOK, c.interceptors.Config())
}

func (c *apiServer) replaceInterceptors(writer http.ResponseWriter, request *http.Request) {
	if !requireAPIJSON(writer, request) {
		return
	}
	var config *InterceptorConfig
	if err := decodeAPIJSONBounded(request.Body, &config, maxInterceptorConfigBytes); err != nil {
		writeAPIError(writer, http.StatusBadRequest, err)
		return
	}
	if config == nil {
		writeAPIError(writer, http.StatusBadRequest, errors.New("interceptor configuration object is required"))
		return
	}
	if err := c.interceptors.Replace(config.Rules); err != nil {
		writeAPIError(writer, http.StatusBadRequest, err)
		return
	}
	writeAPIJSON(writer, http.StatusOK, c.interceptors.Config())
}

func (c *apiServer) setInterceptorEnabled(writer http.ResponseWriter, request *http.Request) {
	if !requireAPIJSON(writer, request) {
		return
	}
	var input struct {
		Name    string `json:"name"`
		Enabled *bool  `json:"enabled"`
	}
	if err := decodeAPIJSON(request.Body, &input); err != nil {
		writeAPIError(writer, http.StatusBadRequest, err)
		return
	}
	if input.Enabled == nil {
		writeAPIError(writer, http.StatusBadRequest, errors.New("enabled is required"))
		return
	}
	rule, err := c.interceptors.SetEnabled(input.Name, *input.Enabled)
	if errors.Is(err, ErrInterceptorNotFound) {
		writeAPIError(writer, http.StatusNotFound, err)
		return
	}
	if err != nil {
		writeAPIError(writer, http.StatusBadRequest, err)
		return
	}
	writeAPIJSON(writer, http.StatusOK, rule)
}

func (c *apiServer) repeat(writer http.ResponseWriter, request *http.Request) {
	if !requireAPIJSON(writer, request) {
		return
	}
	var input RepeatRequest
	if err := decodeAPIJSON(request.Body, &input); err != nil {
		writeAPIError(writer, http.StatusBadRequest, err)
		return
	}
	outgoing, err := c.repeatRequest(request.Context(), input)
	if err != nil {
		writeAPIError(writer, http.StatusBadRequest, err)
		return
	}
	started := time.Now()
	response, err := c.repeatClient.Do(outgoing)
	if err != nil {
		writeAPIError(writer, http.StatusBadGateway, fmt.Errorf("repeat request: %w", err))
		return
	}
	if response == nil || response.Body == nil {
		writeAPIError(writer, http.StatusBadGateway, errors.New("repeat client returned an empty response"))
		return
	}
	defer response.Body.Close()
	body, err := io.ReadAll(io.LimitReader(response.Body, c.maximumBody+1))
	if err != nil {
		writeAPIError(writer, http.StatusBadGateway, fmt.Errorf("read repeated response: %w", err))
		return
	}
	truncated := int64(len(body)) > c.maximumBody
	if truncated {
		body = body[:c.maximumBody]
	}
	writeAPIJSON(writer, http.StatusOK, RepeatResponse{
		StatusCode: response.StatusCode, Headers: response.Header.Clone(),
		BodyBase64: base64.StdEncoding.EncodeToString(body), Truncated: truncated,
		DurationMS: time.Since(started).Milliseconds(),
	})
}

func (c *apiServer) repeatRequest(ctx context.Context, input RepeatRequest) (*http.Request, error) {
	method := strings.ToUpper(strings.TrimSpace(input.Method))
	if method == "" {
		method = http.MethodGet
	}
	if !validHeaderName(method) || method == http.MethodConnect {
		return nil, fmt.Errorf("unsupported repeater method %q", method)
	}
	parsed, err := url.Parse(input.URL)
	if err != nil || parsed.Host == "" || (parsed.Scheme != "http" && parsed.Scheme != "https") {
		return nil, fmt.Errorf("invalid repeater URL %q", input.URL)
	}
	body, err := base64.StdEncoding.DecodeString(input.BodyBase64)
	if err != nil {
		return nil, errors.New("repeater body_base64 is invalid")
	}
	if int64(len(body)) > c.maximumBody {
		return nil, fmt.Errorf("repeater body exceeds %d bytes", c.maximumBody)
	}
	outgoing, err := http.NewRequestWithContext(ctx, method, parsed.String(), bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	if len(input.Headers) > 200 {
		return nil, errors.New("repeater request has more than 200 headers")
	}
	for name, values := range input.Headers {
		canonical := http.CanonicalHeaderKey(name)
		if !validHeaderName(name) || forbiddenRepeaterHeader(canonical) {
			return nil, fmt.Errorf("unsupported repeater header %q", name)
		}
		if len(values) > 100 {
			return nil, fmt.Errorf("repeater header %q has too many values", name)
		}
		for _, value := range values {
			if strings.ContainsAny(value, "\r\n") {
				return nil, fmt.Errorf("invalid repeater header %q", name)
			}
			outgoing.Header.Add(canonical, value)
		}
	}
	return outgoing, nil
}

// RepeatRequest is one edited HTTP request submitted to the proxy repeater.
// BodyBase64 is used so binary request bodies round-trip without coercion.
type RepeatRequest struct {
	Method     string      `json:"method"`
	URL        string      `json:"url"`
	Headers    http.Header `json:"headers,omitempty"`
	BodyBase64 string      `json:"body_base64,omitempty"`
}

// RepeatResponse is the bounded response returned by the proxy repeater.
type RepeatResponse struct {
	StatusCode int         `json:"status_code"`
	Headers    http.Header `json:"headers"`
	BodyBase64 string      `json:"body_base64"`
	Truncated  bool        `json:"truncated"`
	DurationMS int64       `json:"duration_ms"`
}

type historyTransaction struct {
	ID                 uint64      `json:"id"`
	Method             string      `json:"method"`
	URL                string      `json:"url"`
	RequestHeaders     http.Header `json:"request_headers"`
	RequestBodyBase64  string      `json:"request_body_base64"`
	StatusCode         int         `json:"status_code"`
	ResponseHeaders    http.Header `json:"response_headers"`
	ResponseBodyBase64 string      `json:"response_body_base64"`
	DurationMS         int64       `json:"duration_ms"`
	StartedAt          time.Time   `json:"started_at"`
}

type transactionSummary struct {
	ID            uint64    `json:"id"`
	Method        string    `json:"method"`
	URL           string    `json:"url"`
	StatusCode    int       `json:"status_code"`
	RequestBytes  int       `json:"request_bytes"`
	ResponseBytes int       `json:"response_bytes"`
	DurationMS    int64     `json:"duration_ms"`
	StartedAt     time.Time `json:"started_at"`
}

type transactionStats struct {
	Total    int            `json:"total"`
	Methods  map[string]int `json:"methods"`
	Statuses map[int]int    `json:"statuses"`
}

func presentTransaction(captured CapturedTransaction) historyTransaction {
	transaction := captured.Transaction
	return historyTransaction{
		ID: captured.ID, Method: transaction.Method, URL: transaction.URL,
		RequestHeaders:     decodeRecordedHeaders(transaction.RequestHeaders),
		RequestBodyBase64:  base64.StdEncoding.EncodeToString(transaction.RequestBody),
		StatusCode:         transaction.StatusCode,
		ResponseHeaders:    decodeRecordedHeaders(transaction.ResponseHeaders),
		ResponseBodyBase64: base64.StdEncoding.EncodeToString(transaction.ResponseBody),
		DurationMS:         transaction.DurationMS, StartedAt: transaction.StartedAt,
	}
}

func presentTransactionSummary(captured CapturedTransaction) transactionSummary {
	transaction := captured.Transaction
	return transactionSummary{
		ID: captured.ID, Method: transaction.Method, URL: transaction.URL,
		StatusCode: transaction.StatusCode, RequestBytes: len(transaction.RequestBody),
		ResponseBytes: len(transaction.ResponseBody), DurationMS: transaction.DurationMS,
		StartedAt: transaction.StartedAt,
	}
}

func decodeRecordedHeaders(data string) http.Header {
	headers := make(http.Header)
	_ = json.Unmarshal([]byte(data), &headers)
	return headers
}

func parseTransactionFilter(values url.Values) (TransactionFilter, error) {
	for name := range values {
		switch name {
		case "method", "status", "url", "search", "offset", "limit":
		default:
			return TransactionFilter{}, fmt.Errorf("unknown transaction filter %q", name)
		}
	}
	filter := TransactionFilter{
		Method: values.Get("method"), URLContains: values.Get("url"), Search: values.Get("search"), Limit: defaultHistoryLimit,
	}
	filter.Method = strings.ToUpper(strings.TrimSpace(filter.Method))
	if len(filter.Method) > 32 || len(filter.URLContains) > 4096 || len(filter.Search) > 4096 {
		return TransactionFilter{}, errors.New("transaction filter is too long")
	}
	if filter.Method != "" && !validHeaderName(filter.Method) {
		return TransactionFilter{}, errors.New("invalid transaction method")
	}
	var err error
	if value := values.Get("status"); value != "" {
		filter.Status, err = strconv.Atoi(value)
		if err != nil || filter.Status < 100 || filter.Status > 999 {
			return TransactionFilter{}, errors.New("transaction status must be between 100 and 999")
		}
	}
	if value := values.Get("offset"); value != "" {
		filter.Offset, err = strconv.Atoi(value)
		if err != nil || filter.Offset < 0 {
			return TransactionFilter{}, errors.New("transaction offset must be non-negative")
		}
	}
	if value := values.Get("limit"); value != "" {
		filter.Limit, err = strconv.Atoi(value)
		if err != nil || filter.Limit < 1 || filter.Limit > maximumHistoryLimit {
			return TransactionFilter{}, fmt.Errorf("transaction limit must be between 1 and %d", maximumHistoryLimit)
		}
	}
	return filter, nil
}

func decodeAPIJSON(body io.Reader, destination any) error {
	return decodeAPIJSONBounded(body, destination, maximumAPIJSON)
}

func decodeAPIJSONBounded(body io.Reader, destination any, maximum int64) error {
	data, err := io.ReadAll(io.LimitReader(body, maximum+1))
	if err != nil {
		return fmt.Errorf("read JSON: %w", err)
	}
	if int64(len(data)) > maximum {
		return fmt.Errorf("JSON body exceeds %d bytes", maximum)
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(destination); err != nil {
		return fmt.Errorf("decode JSON: %w", err)
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		return errors.New("JSON body must contain one value")
	}
	return nil
}

func requireAPIJSON(writer http.ResponseWriter, request *http.Request) bool {
	mediaType, _, err := mime.ParseMediaType(request.Header.Get("Content-Type"))
	if err == nil && mediaType == "application/json" {
		return true
	}
	writeAPIError(writer, http.StatusUnsupportedMediaType, errors.New("request requires application/json"))
	return false
}

func forbiddenRepeaterHeader(name string) bool {
	switch name {
	case "Connection", "Content-Length", "Host", "Keep-Alive", "Proxy-Authenticate",
		"Proxy-Authorization", "Te", "Trailer", "Transfer-Encoding", "Upgrade":
		return true
	default:
		return false
	}
}

func writeAPIJSON(writer http.ResponseWriter, status int, value any) {
	writer.Header().Set("Content-Type", "application/json")
	writer.WriteHeader(status)
	_ = json.NewEncoder(writer).Encode(value)
}

func writeAPIError(writer http.ResponseWriter, status int, err error) {
	writeAPIJSON(writer, status, map[string]string{"error": err.Error()})
}
