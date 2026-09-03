package har

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"net/http"
	"net/url"
	"sort"
	"strings"
	"time"
)

const MaxEntries = 10_000

// Transaction is the portion of one HAR entry retained by OWTF.
type Transaction struct {
	Method            string
	URL               string
	RequestHeaders    string
	RequestBody       []byte
	RequestMediaType  string
	StatusCode        int
	ResponseHeaders   string
	ResponseBody      []byte
	ResponseMediaType string
	DurationMS        int64
	StartedAt         time.Time
}

type document struct {
	Log struct {
		Version string  `json:"version,omitempty"`
		Creator creator `json:"creator,omitempty"`
		Entries []entry `json:"entries"`
	} `json:"log"`
}

type creator struct {
	Name    string `json:"name"`
	Version string `json:"version"`
}

type entry struct {
	StartedDateTime string  `json:"startedDateTime"`
	Time            float64 `json:"time"`
	Request         struct {
		Method   string   `json:"method"`
		URL      string   `json:"url"`
		Headers  []header `json:"headers"`
		PostData *content `json:"postData"`
	} `json:"request"`
	Response struct {
		Status     int      `json:"status"`
		StatusText string   `json:"statusText,omitempty"`
		Headers    []header `json:"headers"`
		Content    content  `json:"content"`
	} `json:"response"`
}

// Write serializes captured OWTF transactions as a standard HAR 1.2 document.
// Bodies are base64 encoded so arbitrary response bytes round-trip safely.
func Write(writer io.Writer, transactions []Transaction) error {
	if len(transactions) > MaxEntries {
		return fmt.Errorf("cannot write %d transactions; maximum is %d", len(transactions), MaxEntries)
	}
	var output document
	output.Log.Version = "1.2"
	output.Log.Creator = creator{Name: "OWTF", Version: "0.1"}
	output.Log.Entries = make([]entry, 0, len(transactions))
	for index, transaction := range transactions {
		item, err := writeEntry(transaction)
		if err != nil {
			return fmt.Errorf("transaction %d: %w", index+1, err)
		}
		output.Log.Entries = append(output.Log.Entries, item)
	}
	encoder := json.NewEncoder(writer)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(output); err != nil {
		return fmt.Errorf("encode HAR: %w", err)
	}
	return nil
}

func writeEntry(transaction Transaction) (entry, error) {
	if transaction.StartedAt.IsZero() {
		return entry{}, errors.New("started time is required")
	}
	if transaction.DurationMS < 0 {
		return entry{}, errors.New("duration cannot be negative")
	}
	parsedURL, err := url.Parse(transaction.URL)
	if err != nil || parsedURL.Host == "" || (parsedURL.Scheme != "http" && parsedURL.Scheme != "https") {
		return entry{}, fmt.Errorf("invalid HTTP URL %q", transaction.URL)
	}
	requestHeaders, err := decodeHeaders(transaction.RequestHeaders)
	if err != nil {
		return entry{}, fmt.Errorf("request headers: %w", err)
	}
	responseHeaders, err := decodeHeaders(transaction.ResponseHeaders)
	if err != nil {
		return entry{}, fmt.Errorf("response headers: %w", err)
	}
	var item entry
	item.StartedDateTime = transaction.StartedAt.UTC().Format(time.RFC3339Nano)
	item.Time = float64(transaction.DurationMS)
	item.Request.Method = strings.ToUpper(strings.TrimSpace(transaction.Method))
	if item.Request.Method == "" {
		return entry{}, errors.New("request method is required")
	}
	item.Request.URL = parsedURL.String()
	item.Request.Headers = requestHeaders
	if len(transaction.RequestBody) > 0 {
		item.Request.PostData = encodedContent(transaction.RequestBody, transaction.RequestMediaType)
	}
	if transaction.StatusCode < 0 || transaction.StatusCode > 999 {
		return entry{}, fmt.Errorf("invalid response status %d", transaction.StatusCode)
	}
	item.Response.Status = transaction.StatusCode
	item.Response.StatusText = http.StatusText(transaction.StatusCode)
	item.Response.Headers = responseHeaders
	item.Response.Content = *encodedContent(transaction.ResponseBody, transaction.ResponseMediaType)
	return item, nil
}

func decodeHeaders(value string) ([]header, error) {
	if strings.TrimSpace(value) == "" {
		return []header{}, nil
	}
	var values map[string][]string
	if err := json.Unmarshal([]byte(value), &values); err != nil {
		return nil, err
	}
	names := make([]string, 0, len(values))
	for name := range values {
		if strings.TrimSpace(name) == "" {
			return nil, errors.New("header name is empty")
		}
		names = append(names, name)
	}
	sort.Strings(names)
	result := make([]header, 0, len(values))
	for _, name := range names {
		for _, value := range values[name] {
			result = append(result, header{Name: name, Value: value})
		}
	}
	return result, nil
}

func encodedContent(data []byte, mediaType string) *content {
	return &content{
		MimeType: mediaType,
		Text:     base64.StdEncoding.EncodeToString(data),
		Encoding: "base64",
	}
}

type header struct {
	Name  string `json:"name"`
	Value string `json:"value"`
}

type content struct {
	MimeType string `json:"mimeType"`
	Text     string `json:"text"`
	Encoding string `json:"encoding"`
}

// Parse validates and converts a HAR 1.2 document. Unknown HAR fields are
// ignored so browser and proxy extensions remain importable.
func Parse(reader io.Reader) ([]Transaction, error) {
	decoder := json.NewDecoder(reader)
	var input document
	if err := decoder.Decode(&input); err != nil {
		return nil, fmt.Errorf("decode HAR: %w", err)
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		if err == nil {
			return nil, errors.New("decode HAR: multiple JSON values")
		}
		return nil, fmt.Errorf("decode HAR trailing data: %w", err)
	}
	if len(input.Log.Entries) == 0 {
		return nil, errors.New("HAR contains no transactions")
	}
	if len(input.Log.Entries) > MaxEntries {
		return nil, fmt.Errorf("HAR contains %d transactions; maximum is %d", len(input.Log.Entries), MaxEntries)
	}

	transactions := make([]Transaction, 0, len(input.Log.Entries))
	for index, item := range input.Log.Entries {
		transaction, err := parseEntry(item)
		if err != nil {
			return nil, fmt.Errorf("HAR transaction %d: %w", index+1, err)
		}
		transactions = append(transactions, transaction)
	}
	return transactions, nil
}

func parseEntry(item entry) (Transaction, error) {
	method := strings.TrimSpace(item.Request.Method)
	if method == "" {
		return Transaction{}, errors.New("request method is required")
	}
	parsedURL, err := url.Parse(item.Request.URL)
	if err != nil || parsedURL.Host == "" || (parsedURL.Scheme != "http" && parsedURL.Scheme != "https") {
		return Transaction{}, fmt.Errorf("invalid HTTP URL %q", item.Request.URL)
	}
	started, err := time.Parse(time.RFC3339Nano, item.StartedDateTime)
	if err != nil {
		return Transaction{}, fmt.Errorf("invalid startedDateTime %q", item.StartedDateTime)
	}
	if math.IsNaN(item.Time) || math.IsInf(item.Time, 0) || item.Time < 0 {
		return Transaction{}, fmt.Errorf("invalid duration %v", item.Time)
	}
	if item.Response.Status < 0 || item.Response.Status > 999 {
		return Transaction{}, fmt.Errorf("invalid response status %d", item.Response.Status)
	}
	requestHeaders, err := encodeHeaders(item.Request.Headers)
	if err != nil {
		return Transaction{}, fmt.Errorf("request headers: %w", err)
	}
	responseHeaders, err := encodeHeaders(item.Response.Headers)
	if err != nil {
		return Transaction{}, fmt.Errorf("response headers: %w", err)
	}
	var requestBody []byte
	var requestMediaType string
	if item.Request.PostData != nil {
		requestBody, err = decodeContent(*item.Request.PostData)
		if err != nil {
			return Transaction{}, fmt.Errorf("request body: %w", err)
		}
		requestMediaType = item.Request.PostData.MimeType
	}
	responseBody, err := decodeContent(item.Response.Content)
	if err != nil {
		return Transaction{}, fmt.Errorf("response body: %w", err)
	}
	return Transaction{
		Method: strings.ToUpper(method), URL: parsedURL.String(), RequestHeaders: requestHeaders,
		RequestBody: requestBody, RequestMediaType: requestMediaType, StatusCode: item.Response.Status,
		ResponseHeaders: responseHeaders, ResponseBody: responseBody,
		ResponseMediaType: item.Response.Content.MimeType, DurationMS: int64(math.Round(item.Time)),
		StartedAt: started.UTC(),
	}, nil
}

func encodeHeaders(values []header) (string, error) {
	headers := make(http.Header)
	for _, item := range values {
		name := strings.TrimSpace(item.Name)
		if name == "" {
			return "", errors.New("header name is empty")
		}
		headers.Add(name, item.Value)
	}
	data, err := json.Marshal(headers)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

func decodeContent(value content) ([]byte, error) {
	switch strings.ToLower(strings.TrimSpace(value.Encoding)) {
	case "":
		return []byte(value.Text), nil
	case "base64":
		data, err := base64.StdEncoding.DecodeString(value.Text)
		if err != nil {
			return nil, fmt.Errorf("invalid base64: %w", err)
		}
		return data, nil
	default:
		return nil, fmt.Errorf("unsupported encoding %q", value.Encoding)
	}
}
