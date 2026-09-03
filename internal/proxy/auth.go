package proxy

import (
	"crypto/md5"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
)

// Credentials are HTTP authentication credentials for one target host.
type Credentials struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// OriginAuthTransport answers Basic and Digest authentication challenges for
// configured target hosts. It does not send credentials to unlisted hosts.
type OriginAuthTransport struct {
	next        http.RoundTripper
	credentials map[string]Credentials
}

// NewOriginAuthTransport validates and copies host credentials.
func NewOriginAuthTransport(next http.RoundTripper, credentials map[string]Credentials) (*OriginAuthTransport, error) {
	if next == nil {
		next = http.DefaultTransport
	}
	configured := make(map[string]Credentials, len(credentials))
	for host, credential := range credentials {
		host = canonicalHost(host)
		if host == "" || strings.ContainsAny(host, "/\\ 	\r\n") {
			return nil, errors.New("HTTP authentication host is invalid")
		}
		if credential.Username == "" || strings.ContainsAny(credential.Username, "\r\n") {
			return nil, fmt.Errorf("HTTP authentication username for %s is invalid", host)
		}
		if _, duplicate := configured[host]; duplicate {
			return nil, fmt.Errorf("duplicate HTTP authentication host %s", host)
		}
		configured[host] = credential
	}
	return &OriginAuthTransport{next: next, credentials: configured}, nil
}

// RoundTrip implements http.RoundTripper.
func (t OriginAuthTransport) RoundTrip(request *http.Request) (*http.Response, error) {
	credentials, ok := t.credentials[canonicalHost(request.URL.Hostname())]
	if !ok {
		return t.next.RoundTrip(request)
	}
	response, err := t.next.RoundTrip(request)
	if err != nil || response == nil || response.StatusCode != http.StatusUnauthorized {
		return response, err
	}
	authorized, err := authenticatedRequest(request, response.Header.Values("WWW-Authenticate"), credentials)
	if errors.Is(err, errNoSupportedChallenge) || errors.Is(err, errBodyNotReplayable) {
		return response, nil
	}
	if err != nil {
		response.Body.Close()
		return nil, err
	}
	_, _ = io.Copy(io.Discard, io.LimitReader(response.Body, 4<<10))
	response.Body.Close()
	return t.next.RoundTrip(authorized)
}

var (
	errNoSupportedChallenge = errors.New("no supported HTTP authentication challenge")
	errBodyNotReplayable    = errors.New("request body cannot be replayed for HTTP authentication")
)

func authenticatedRequest(request *http.Request, challenges []string, credentials Credentials) (*http.Request, error) {
	authorized, err := replayRequest(request)
	if err != nil {
		return nil, err
	}
	if challenge, ok := findChallenge(challenges, "digest"); ok {
		header, err := digestAuthorization(request, challenge, credentials)
		if err != nil {
			return nil, err
		}
		authorized.Header.Set("Authorization", header)
		return authorized, nil
	}
	if _, ok := findChallenge(challenges, "basic"); ok {
		authorized.SetBasicAuth(credentials.Username, credentials.Password)
		return authorized, nil
	}
	return nil, errNoSupportedChallenge
}

func replayRequest(request *http.Request) (*http.Request, error) {
	copy := request.Clone(request.Context())
	if request.Body == nil {
		return copy, nil
	}
	if request.GetBody == nil {
		return nil, errBodyNotReplayable
	}
	body, err := request.GetBody()
	if err != nil {
		return nil, fmt.Errorf("replay request body for HTTP authentication: %w", err)
	}
	copy.Body = body
	return copy, nil
}

func findChallenge(values []string, scheme string) (string, bool) {
	for _, value := range values {
		trimmed := strings.TrimSpace(value)
		if len(trimmed) <= len(scheme) || !strings.EqualFold(trimmed[:len(scheme)], scheme) {
			continue
		}
		if trimmed[len(scheme)] == ' ' || trimmed[len(scheme)] == '\t' {
			return strings.TrimSpace(trimmed[len(scheme):]), true
		}
	}
	return "", false
}

func digestAuthorization(request *http.Request, challenge string, credentials Credentials) (string, error) {
	parameters, err := parseAuthParameters(challenge)
	if err != nil {
		return "", fmt.Errorf("parse Digest challenge: %w", err)
	}
	realm, nonce := parameters["realm"], parameters["nonce"]
	if realm == "" || nonce == "" {
		return "", errors.New("Digest challenge requires realm and nonce")
	}
	if strings.EqualFold(parameters["userhash"], "true") {
		return "", errors.New("Digest userhash is not supported")
	}
	algorithm := strings.ToUpper(parameters["algorithm"])
	if algorithm == "" {
		algorithm = "MD5"
	}
	hash, session, err := digestHash(algorithm)
	if err != nil {
		return "", err
	}
	qop, err := digestQOP(parameters["qop"])
	if err != nil {
		return "", err
	}
	cnonce, err := randomHex(16)
	if err != nil {
		return "", err
	}
	uri := request.URL.RequestURI()
	if uri == "" {
		uri = "/"
	}
	ha1 := hash(credentials.Username + ":" + realm + ":" + credentials.Password)
	if session {
		ha1 = hash(ha1 + ":" + nonce + ":" + cnonce)
	}
	ha2 := hash(request.Method + ":" + uri)
	response := ""
	if qop == "" {
		response = hash(ha1 + ":" + nonce + ":" + ha2)
	} else {
		response = hash(ha1 + ":" + nonce + ":00000001:" + cnonce + ":" + qop + ":" + ha2)
	}
	fields := []string{
		`username="` + quoteAuth(credentials.Username) + `"`,
		`realm="` + quoteAuth(realm) + `"`,
		`nonce="` + quoteAuth(nonce) + `"`,
		`uri="` + quoteAuth(uri) + `"`,
		`response="` + response + `"`,
		"algorithm=" + algorithm,
	}
	if opaque := parameters["opaque"]; opaque != "" {
		fields = append(fields, `opaque="`+quoteAuth(opaque)+`"`)
	}
	if qop != "" {
		fields = append(fields, "qop="+qop, "nc=00000001", `cnonce="`+cnonce+`"`)
	}
	return "Digest " + strings.Join(fields, ", "), nil
}

func digestHash(algorithm string) (func(string) string, bool, error) {
	session := strings.HasSuffix(algorithm, "-SESS")
	base := strings.TrimSuffix(algorithm, "-SESS")
	switch base {
	case "MD5":
		return func(value string) string {
			sum := md5.Sum([]byte(value))
			return hex.EncodeToString(sum[:])
		}, session, nil
	case "SHA-256":
		return func(value string) string {
			sum := sha256.Sum256([]byte(value))
			return hex.EncodeToString(sum[:])
		}, session, nil
	default:
		return nil, false, fmt.Errorf("unsupported Digest algorithm %q", algorithm)
	}
}

func digestQOP(value string) (string, error) {
	if strings.TrimSpace(value) == "" {
		return "", nil
	}
	for _, item := range strings.Split(value, ",") {
		if strings.EqualFold(strings.TrimSpace(item), "auth") {
			return "auth", nil
		}
	}
	return "", fmt.Errorf("unsupported Digest qop %q", value)
}

func parseAuthParameters(value string) (map[string]string, error) {
	parameters := make(map[string]string)
	for offset := 0; ; {
		for offset < len(value) && (value[offset] == ' ' || value[offset] == '\t' || value[offset] == ',') {
			offset++
		}
		if offset == len(value) {
			return parameters, nil
		}
		start := offset
		for offset < len(value) && isAuthToken(value[offset]) {
			offset++
		}
		if start == offset {
			return nil, fmt.Errorf("unexpected byte at offset %d", offset)
		}
		name := strings.ToLower(value[start:offset])
		for offset < len(value) && (value[offset] == ' ' || value[offset] == '\t') {
			offset++
		}
		if offset == len(value) || value[offset] != '=' {
			return nil, fmt.Errorf("parameter %q has no value", name)
		}
		offset++
		for offset < len(value) && (value[offset] == ' ' || value[offset] == '\t') {
			offset++
		}
		parameter, next, err := parseAuthValue(value, offset)
		if err != nil {
			return nil, fmt.Errorf("parameter %q: %w", name, err)
		}
		if _, duplicate := parameters[name]; duplicate {
			return nil, fmt.Errorf("duplicate parameter %q", name)
		}
		parameters[name], offset = parameter, next
	}
}

func parseAuthValue(value string, offset int) (string, int, error) {
	if offset == len(value) {
		return "", offset, nil
	}
	if value[offset] != '"' {
		start := offset
		for offset < len(value) && value[offset] != ',' && value[offset] != ' ' && value[offset] != '\t' {
			offset++
		}
		return value[start:offset], offset, nil
	}
	offset++
	var result strings.Builder
	for offset < len(value) {
		switch value[offset] {
		case '"':
			return result.String(), offset + 1, nil
		case '\\':
			offset++
			if offset == len(value) {
				return "", offset, errors.New("unterminated escape")
			}
			result.WriteByte(value[offset])
		default:
			result.WriteByte(value[offset])
		}
		offset++
	}
	return "", offset, errors.New("unterminated quoted value")
}

func isAuthToken(value byte) bool {
	return value >= 'a' && value <= 'z' || value >= 'A' && value <= 'Z' ||
		value >= '0' && value <= '9' || strings.ContainsRune("!#$%&'*+-.^_`|~", rune(value))
}

func quoteAuth(value string) string {
	value = strings.ReplaceAll(value, `\`, `\\`)
	return strings.ReplaceAll(value, `"`, `\"`)
}

func randomHex(size int) (string, error) {
	data := make([]byte, size)
	if _, err := rand.Read(data); err != nil {
		return "", fmt.Errorf("generate Digest nonce: %w", err)
	}
	return hex.EncodeToString(data), nil
}
