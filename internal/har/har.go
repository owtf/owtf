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
		Entries []entry `json:"entries"`
	} `json:"log"`
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
		Status  int      `json:"status"`
		Headers []header `json:"headers"`
		Content content  `json:"content"`
	} `json:"response"`
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
