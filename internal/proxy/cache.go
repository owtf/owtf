package proxy

import (
	"bytes"
	"container/list"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"net/http"
	"sort"
	"strings"
	"sync"
)

// CacheOptions bounds response storage and controls which cookies contribute
// to cache identity. Filtering never changes the forwarded Cookie header.
type CacheOptions struct {
	MaximumEntries  int
	MaximumBody     int64
	CookieBlacklist []string
	CookieWhitelist []string
}

// ResponseCache is a bounded, concurrency-safe least-recently-used cache.
type ResponseCache struct {
	mu        sync.Mutex
	entries   map[string]*list.Element
	recent    list.List
	maximum   int
	maxBody   int64
	blacklist map[string]bool
	whitelist map[string]bool
}

type cacheEntry struct {
	key      string
	response cachedResponse
}

type cachedResponse struct {
	status        string
	statusCode    int
	protocol      string
	protocolMajor int
	protocolMinor int
	headers       http.Header
	body          []byte
	contentLength int64
	transfer      []string
	trailer       http.Header
}

// NewResponseCache creates a response cache with explicit memory bounds.
func NewResponseCache(options CacheOptions) (*ResponseCache, error) {
	if options.MaximumEntries < 1 {
		return nil, fmt.Errorf("cache maximum entries must be positive")
	}
	if options.MaximumBody < 1 {
		return nil, fmt.Errorf("cache maximum body must be positive")
	}
	return &ResponseCache{
		entries: make(map[string]*list.Element, options.MaximumEntries),
		maximum: options.MaximumEntries, maxBody: options.MaximumBody,
		blacklist: names(options.CookieBlacklist), whitelist: names(options.CookieWhitelist),
	}, nil
}

// RoundTripper wraps an upstream transport with this cache.
func (c *ResponseCache) RoundTripper(next http.RoundTripper) http.RoundTripper {
	if next == nil {
		next = http.DefaultTransport
	}
	return cacheTransport{cache: c, next: next}
}

// Clear removes every cached response.
func (c *ResponseCache) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()
	clear(c.entries)
	c.recent.Init()
}

func (c *ResponseCache) get(key string, request *http.Request) (*http.Response, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	element, ok := c.entries[key]
	if !ok {
		return nil, false
	}
	c.recent.MoveToFront(element)
	return element.Value.(*cacheEntry).response.toHTTP(request), true
}

func (c *ResponseCache) put(key string, response cachedResponse) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if element, ok := c.entries[key]; ok {
		element.Value.(*cacheEntry).response = response
		c.recent.MoveToFront(element)
		return
	}
	element := c.recent.PushFront(&cacheEntry{key: key, response: response})
	c.entries[key] = element
	if c.recent.Len() <= c.maximum {
		return
	}
	oldest := c.recent.Back()
	delete(c.entries, oldest.Value.(*cacheEntry).key)
	c.recent.Remove(oldest)
}

type cacheTransport struct {
	cache *ResponseCache
	next  http.RoundTripper
}

func (t cacheTransport) RoundTrip(request *http.Request) (*http.Response, error) {
	if request.Method != http.MethodGet && request.Method != http.MethodHead {
		return t.next.RoundTrip(request)
	}
	key := t.cache.key(request)
	if response, ok := t.cache.get(key, request); ok {
		return response, nil
	}
	response, err := t.next.RoundTrip(request)
	if err != nil || response == nil || !cacheable(response) {
		return response, err
	}
	body, complete, readErr := readBounded(response.Body, t.cache.maxBody)
	if readErr != nil {
		response.Body.Close()
		return nil, readErr
	}
	if !complete {
		response.Body = io.NopCloser(io.MultiReader(bytes.NewReader(body), response.Body))
		return response, nil
	}
	if err := response.Body.Close(); err != nil {
		return nil, err
	}
	snapshot := responseSnapshot(response, body)
	t.cache.put(key, snapshot)
	return snapshot.toHTTP(request), nil
}

func (c *ResponseCache) key(request *http.Request) string {
	hash := sha256.New()
	_, _ = io.WriteString(hash, request.Method)
	_, _ = io.WriteString(hash, "\x00")
	_, _ = io.WriteString(hash, request.URL.String())
	names := make([]string, 0, len(request.Header))
	for name := range request.Header {
		names = append(names, http.CanonicalHeaderKey(name))
	}
	sort.Strings(names)
	for _, name := range names {
		values := request.Header.Values(name)
		if name == "Cookie" {
			values = []string{c.filteredCookies(request.Cookies())}
		}
		for _, value := range values {
			_, _ = io.WriteString(hash, "\x00"+name+"\x00"+value)
		}
	}
	return hex.EncodeToString(hash.Sum(nil))
}

func (c *ResponseCache) filteredCookies(cookies []*http.Cookie) string {
	values := make([]string, 0, len(cookies))
	for _, cookie := range cookies {
		name := strings.ToLower(cookie.Name)
		if c.blacklist[name] || len(c.whitelist) > 0 && !c.whitelist[name] {
			continue
		}
		values = append(values, cookie.Name+"="+cookie.Value)
	}
	sort.Strings(values)
	return strings.Join(values, "; ")
}

func responseSnapshot(response *http.Response, body []byte) cachedResponse {
	return cachedResponse{
		status: response.Status, statusCode: response.StatusCode,
		protocol: response.Proto, protocolMajor: response.ProtoMajor, protocolMinor: response.ProtoMinor,
		headers: response.Header.Clone(), body: append([]byte(nil), body...),
		contentLength: response.ContentLength, transfer: append([]string(nil), response.TransferEncoding...),
		trailer: response.Trailer.Clone(),
	}
}

func (response cachedResponse) toHTTP(request *http.Request) *http.Response {
	return &http.Response{
		Status: response.status, StatusCode: response.statusCode,
		Proto: response.protocol, ProtoMajor: response.protocolMajor, ProtoMinor: response.protocolMinor,
		Header: response.headers.Clone(), Body: io.NopCloser(bytes.NewReader(response.body)),
		ContentLength: response.contentLength, TransferEncoding: append([]string(nil), response.transfer...),
		Trailer: response.trailer.Clone(), Request: request,
	}
}

func cacheable(response *http.Response) bool {
	if response.StatusCode < 200 || response.StatusCode >= 400 {
		return false
	}
	for _, directive := range strings.Split(response.Header.Get("Cache-Control"), ",") {
		if strings.EqualFold(strings.TrimSpace(directive), "no-store") {
			return false
		}
	}
	return true
}

func readBounded(reader io.Reader, maximum int64) ([]byte, bool, error) {
	data, err := io.ReadAll(io.LimitReader(reader, maximum+1))
	if err != nil {
		return nil, false, err
	}
	if int64(len(data)) > maximum {
		return data, false, nil
	}
	return data, true, nil
}

func names(values []string) map[string]bool {
	result := make(map[string]bool, len(values))
	for _, value := range values {
		if value = strings.ToLower(strings.TrimSpace(value)); value != "" {
			result[value] = true
		}
	}
	return result
}
