package proxy

import (
	"bufio"
	"bytes"
	"crypto/tls"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"github.com/owtf/owtf/internal/har"
)

const defaultMaximumBody = 1 << 20

// TransactionRecorder accepts completed proxy transactions.
type TransactionRecorder interface {
	Record(har.Transaction) error
}

// Config defines the dependencies and bounds of one proxy instance.
type Config struct {
	Authority    *Authority
	Recorder     TransactionRecorder
	Transport    http.RoundTripper
	AllowedHosts []string
	MaximumBody  int64
	Interceptors *Interceptors
	ErrorLog     *log.Logger
}

// Proxy forwards HTTP and HTTPS requests and records their transactions.
type Proxy struct {
	authority    *Authority
	recorder     TransactionRecorder
	transport    http.RoundTripper
	allowedHosts map[string]bool
	maximumBody  int64
	interceptors *Interceptors
	errorLog     *log.Logger
}

// New creates an OWTF proxy. An empty host list preserves the interactive
// proxy's historical behavior; callers may provide hosts for task isolation.
func New(config Config) (*Proxy, error) {
	if config.Authority == nil {
		return nil, errors.New("proxy authority is required")
	}
	if config.Recorder == nil {
		return nil, errors.New("proxy transaction recorder is required")
	}
	if config.Transport == nil {
		transport := http.DefaultTransport.(*http.Transport).Clone()
		transport.DisableCompression = true
		config.Transport = transport
	}
	if config.MaximumBody <= 0 {
		config.MaximumBody = defaultMaximumBody
	}
	if config.ErrorLog == nil {
		config.ErrorLog = log.New(io.Discard, "", 0)
	}
	allowedHosts := make(map[string]bool, len(config.AllowedHosts))
	for _, host := range config.AllowedHosts {
		if host = canonicalHost(host); host != "" {
			allowedHosts[host] = true
		}
	}
	return &Proxy{
		authority: config.Authority, recorder: config.Recorder, transport: config.Transport,
		allowedHosts: allowedHosts, maximumBody: config.MaximumBody,
		interceptors: config.Interceptors, errorLog: config.ErrorLog,
	}, nil
}

// ServeHTTP handles ordinary proxy requests and HTTPS CONNECT interception.
func (p *Proxy) ServeHTTP(writer http.ResponseWriter, request *http.Request) {
	if request.Method == http.MethodConnect {
		p.connect(writer, request)
		return
	}
	if request.URL == nil || (request.URL.Scheme != "http" && request.URL.Scheme != "https") || request.URL.Host == "" {
		http.Error(writer, "OWTF proxy requires an absolute HTTP URL", http.StatusBadRequest)
		return
	}
	if !p.hostAllowed(request.URL.Hostname()) {
		http.Error(writer, "target host is outside this proxy scope", http.StatusForbidden)
		return
	}
	p.forward(writer, request, request.URL.Scheme, request.URL.Host)
}

func (p *Proxy) forward(writer http.ResponseWriter, request *http.Request, scheme, authority string) {
	started := time.Now().UTC()
	outgoing := request.Clone(request.Context())
	outgoing.URL = cloneURL(request)
	if outgoing.URL.Scheme == "" {
		outgoing.URL.Scheme = scheme
	}
	if outgoing.URL.Host == "" {
		outgoing.URL.Host = authority
	}
	outgoing.RequestURI = ""
	outgoing.Header = request.Header.Clone()
	if err := p.interceptors.InterceptRequest(request.Context(), outgoing); err != nil {
		p.interceptionError(writer, "request", err)
		return
	}
	if !p.hostAllowed(outgoing.URL.Hostname()) {
		http.Error(writer, "interceptor rewrote request outside this proxy scope", http.StatusForbidden)
		return
	}
	upgrade := isUpgrade(outgoing.Header)
	if !upgrade {
		removeHopHeaders(outgoing.Header)
	} else {
		outgoing.Header.Del("Proxy-Connection")
	}

	requestBody := newPrefixWriter(p.maximumBody)
	if outgoing.Body != nil {
		outgoing.Body = &teeReadCloser{Reader: io.TeeReader(outgoing.Body, requestBody), Closer: outgoing.Body}
	}
	response, err := p.transport.RoundTrip(outgoing)
	if err != nil {
		p.errorLog.Printf("proxy %s %s: %v", request.Method, outgoing.URL.Redacted(), err)
		http.Error(writer, "upstream request failed", http.StatusBadGateway)
		return
	}
	defer response.Body.Close()
	if response.Request == nil {
		response.Request = outgoing
	}
	// An upgraded response body is the live bidirectional stream. Never pass it
	// through body interceptors before handing ownership to the tunnel.
	if response.StatusCode == http.StatusSwitchingProtocols && upgrade {
		p.record(started, outgoing, response, requestBody.Bytes(), nil)
		p.upgrade(writer, response)
		return
	}
	if err := p.interceptors.InterceptResponse(request.Context(), response); err != nil {
		p.interceptionError(writer, "response", err)
		return
	}
	copyHeaders(writer.Header(), response.Header, false)
	writer.WriteHeader(response.StatusCode)
	responseBody := newPrefixWriter(p.maximumBody)
	if _, err := io.Copy(writer, io.TeeReader(response.Body, responseBody)); err != nil {
		p.errorLog.Printf("proxy response %s: %v", outgoing.URL.Redacted(), err)
	}
	p.record(started, outgoing, response, requestBody.Bytes(), responseBody.Bytes())
}

func (p *Proxy) interceptionError(writer http.ResponseWriter, phase string, err error) {
	p.errorLog.Printf("proxy %s interceptor: %v", phase, err)
	status := http.StatusBadGateway
	if phase == "request" {
		status = http.StatusBadRequest
	}
	if errors.Is(err, ErrInterceptorBodyTooLarge) {
		status = http.StatusRequestEntityTooLarge
	}
	http.Error(writer, phase+" interception failed", status)
}

func (p *Proxy) connect(writer http.ResponseWriter, request *http.Request) {
	authority := request.Host
	if authority == "" {
		authority = request.RequestURI
	}
	host := canonicalHost(authority)
	if host == "" {
		http.Error(writer, "CONNECT host is required", http.StatusBadRequest)
		return
	}
	if !p.hostAllowed(host) {
		http.Error(writer, "target host is outside this proxy scope", http.StatusForbidden)
		return
	}
	certificate, err := p.authority.certificateForHost(host)
	if err != nil {
		p.errorLog.Printf("proxy certificate %s: %v", host, err)
		http.Error(writer, "could not create interception certificate", http.StatusBadGateway)
		return
	}
	hijacker, ok := writer.(http.Hijacker)
	if !ok {
		http.Error(writer, "proxy connection cannot be intercepted", http.StatusInternalServerError)
		return
	}
	connection, buffered, err := hijacker.Hijack()
	if err != nil {
		p.errorLog.Printf("proxy CONNECT hijack %s: %v", host, err)
		return
	}
	if _, err := buffered.WriteString("HTTP/1.1 200 Connection Established\r\n\r\n"); err != nil {
		connection.Close()
		return
	}
	if err := buffered.Flush(); err != nil {
		connection.Close()
		return
	}

	intercepted := tls.Server(&bufferedConn{Conn: connection, reader: buffered.Reader}, &tls.Config{
		Certificates: []tls.Certificate{certificate}, MinVersion: tls.VersionTLS12,
		NextProtos: []string{"http/1.1"},
	})
	_ = intercepted.SetDeadline(time.Now().Add(10 * time.Second))
	if err := intercepted.HandshakeContext(request.Context()); err != nil {
		p.errorLog.Printf("proxy TLS handshake %s: %v", host, err)
		intercepted.Close()
		return
	}
	_ = intercepted.SetDeadline(time.Time{})

	listener := newSingleConnListener(intercepted)
	server := &http.Server{
		Handler: http.HandlerFunc(func(innerWriter http.ResponseWriter, innerRequest *http.Request) {
			if innerRequest.Host == "" {
				innerRequest.Host = authority
			}
			p.forward(innerWriter, innerRequest, "https", authority)
		}),
		ReadHeaderTimeout: 10 * time.Second,
		IdleTimeout:       60 * time.Second,
		ErrorLog:          p.errorLog,
	}
	_ = server.Serve(listener)
}

func (p *Proxy) upgrade(writer http.ResponseWriter, response *http.Response) {
	upstream, ok := response.Body.(io.ReadWriteCloser)
	if !ok {
		http.Error(writer, "upstream upgrade is not bidirectional", http.StatusBadGateway)
		return
	}
	hijacker, ok := writer.(http.Hijacker)
	if !ok {
		http.Error(writer, "client connection cannot be upgraded", http.StatusInternalServerError)
		return
	}
	client, buffered, err := hijacker.Hijack()
	if err != nil {
		return
	}
	defer client.Close()
	defer upstream.Close()
	if _, err := fmt.Fprintf(buffered, "%s %s\r\n", response.Proto, response.Status); err != nil {
		return
	}
	if err := response.Header.Write(buffered); err != nil {
		return
	}
	if _, err := buffered.WriteString("\r\n"); err != nil {
		return
	}
	if err := buffered.Flush(); err != nil {
		return
	}

	clientStream := &bufferedReadWriter{Reader: buffered.Reader, Writer: client}
	done := make(chan struct{}, 2)
	go func() {
		_, _ = io.Copy(upstream, clientStream)
		done <- struct{}{}
	}()
	go func() {
		_, _ = io.Copy(clientStream, upstream)
		done <- struct{}{}
	}()
	<-done
	_ = client.Close()
	_ = upstream.Close()
	<-done
}

func (p *Proxy) record(started time.Time, request *http.Request, response *http.Response, requestBody, responseBody []byte) {
	requestHeaders, _ := json.Marshal(request.Header)
	responseHeaders, _ := json.Marshal(response.Header)
	transaction := har.Transaction{
		Method: request.Method, URL: request.URL.String(), RequestHeaders: string(requestHeaders),
		RequestBody: requestBody, RequestMediaType: request.Header.Get("Content-Type"),
		StatusCode: response.StatusCode, ResponseHeaders: string(responseHeaders),
		ResponseBody: responseBody, ResponseMediaType: response.Header.Get("Content-Type"),
		DurationMS: time.Since(started).Milliseconds(), StartedAt: started,
	}
	if err := p.recorder.Record(transaction); err != nil {
		p.errorLog.Printf("record proxy transaction: %v", err)
	}
}

func (p *Proxy) hostAllowed(host string) bool {
	return len(p.allowedHosts) == 0 || p.allowedHosts[canonicalHost(host)]
}

func canonicalHost(authority string) string {
	authority = strings.TrimSpace(authority)
	if host, _, err := net.SplitHostPort(authority); err == nil {
		return strings.ToLower(strings.Trim(host, "[]"))
	}
	return strings.ToLower(strings.Trim(authority, "[]"))
}

func cloneURL(request *http.Request) *url.URL {
	if request.URL == nil {
		return &url.URL{}
	}
	copy := *request.URL
	return &copy
}

func removeHopHeaders(headers http.Header) {
	for _, name := range strings.Split(headers.Get("Connection"), ",") {
		if name = strings.TrimSpace(name); name != "" {
			headers.Del(name)
		}
	}
	for _, name := range []string{
		"Connection", "Proxy-Connection", "Keep-Alive", "Proxy-Authenticate",
		"Proxy-Authorization", "TE", "Trailer", "Transfer-Encoding", "Upgrade",
	} {
		headers.Del(name)
	}
}

func copyHeaders(destination, source http.Header, preserveUpgrade bool) {
	copy := source.Clone()
	if !preserveUpgrade {
		removeHopHeaders(copy)
	}
	for name, values := range copy {
		for _, value := range values {
			destination.Add(name, value)
		}
	}
}

func isUpgrade(headers http.Header) bool {
	if strings.TrimSpace(headers.Get("Upgrade")) == "" {
		return false
	}
	for _, value := range strings.Split(headers.Get("Connection"), ",") {
		if strings.EqualFold(strings.TrimSpace(value), "upgrade") {
			return true
		}
	}
	return false
}

type prefixWriter struct {
	mu        sync.Mutex
	remaining int64
	buffer    bytes.Buffer
}

func newPrefixWriter(maximum int64) *prefixWriter {
	return &prefixWriter{remaining: maximum}
}

func (w *prefixWriter) Write(data []byte) (int, error) {
	w.mu.Lock()
	defer w.mu.Unlock()
	original := len(data)
	if int64(len(data)) > w.remaining {
		data = data[:w.remaining]
	}
	if len(data) > 0 {
		_, _ = w.buffer.Write(data)
		w.remaining -= int64(len(data))
	}
	return original, nil
}

func (w *prefixWriter) Bytes() []byte {
	w.mu.Lock()
	defer w.mu.Unlock()
	return append([]byte(nil), w.buffer.Bytes()...)
}

type teeReadCloser struct {
	io.Reader
	io.Closer
}

type bufferedConn struct {
	net.Conn
	reader *bufio.Reader
}

func (c *bufferedConn) Read(data []byte) (int, error) { return c.reader.Read(data) }

type bufferedReadWriter struct {
	io.Reader
	io.Writer
}

type notifiedConn struct {
	net.Conn
	closed chan struct{}
	once   sync.Once
}

func (c *notifiedConn) Close() error {
	c.once.Do(func() { close(c.closed) })
	return c.Conn.Close()
}

type singleConnListener struct {
	connection *notifiedConn
	mu         sync.Mutex
	accepted   bool
}

func newSingleConnListener(connection net.Conn) *singleConnListener {
	return &singleConnListener{connection: &notifiedConn{Conn: connection, closed: make(chan struct{})}}
}

func (l *singleConnListener) Accept() (net.Conn, error) {
	l.mu.Lock()
	if !l.accepted {
		l.accepted = true
		l.mu.Unlock()
		return l.connection, nil
	}
	l.mu.Unlock()
	<-l.connection.closed
	return nil, net.ErrClosed
}

func (l *singleConnListener) Close() error   { return l.connection.Close() }
func (l *singleConnListener) Addr() net.Addr { return l.connection.LocalAddr() }
