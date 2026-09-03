package proxy

import (
	"encoding/base64"
	"io"
	"net/http"
	"strings"
	"testing"
)

func TestOriginAuthTransportAnswersBasicChallenge(t *testing.T) {
	attempts := 0
	transport, err := NewOriginAuthTransport(
		roundTripperFunc(func(request *http.Request) (*http.Response, error) {
			attempts++
			if attempts == 1 {
				response := testResponse(request, http.StatusUnauthorized, "authenticate")
				response.Header.Set("WWW-Authenticate", `Basic realm="OWTF"`)
				return response, nil
			}
			want := "Basic " + base64.StdEncoding.EncodeToString([]byte("operator:secret"))
			if got := request.Header.Get("Authorization"); got != want {
				t.Fatalf("Authorization = %q, want %q", got, want)
			}
			return testResponse(request, http.StatusOK, "authorized"), nil
		}), map[string]Credentials{"EXAMPLE.test:443": {Username: "operator", Password: "secret"}},
	)
	if err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodGet, "https://example.test/private", nil)
	response, err := transport.RoundTrip(request)
	if err != nil {
		t.Fatal(err)
	}
	response.Body.Close()
	if attempts != 2 || response.StatusCode != http.StatusOK {
		t.Fatalf("attempts = %d, status = %d", attempts, response.StatusCode)
	}
}

func TestOriginAuthTransportAnswersDigestChallenge(t *testing.T) {
	attempts := 0
	transport, err := NewOriginAuthTransport(
		roundTripperFunc(func(request *http.Request) (*http.Response, error) {
			attempts++
			if attempts == 1 {
				response := testResponse(request, http.StatusUnauthorized, "authenticate")
				response.Header.Set("WWW-Authenticate", `Digest realm="testrealm@host.com", qop="auth,auth-int", nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", opaque="5ccc069c403ebaf9f0171e9517f40e41"`)
				return response, nil
			}
			header := request.Header.Get("Authorization")
			for _, want := range []string{
				`Digest username="Mufasa"`, `realm="testrealm@host.com"`, `uri="/dir/index.html"`,
				`algorithm=MD5`, `qop=auth`, `nc=00000001`, `cnonce="`, `response="`,
			} {
				if !strings.Contains(header, want) {
					t.Fatalf("Digest Authorization does not contain %q: %s", want, header)
				}
			}
			return testResponse(request, http.StatusOK, "authorized"), nil
		}), map[string]Credentials{"example.test": {Username: "Mufasa", Password: "Circle Of Life"}},
	)
	if err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodGet, "http://example.test/dir/index.html", nil)
	response, err := transport.RoundTrip(request)
	if err != nil {
		t.Fatal(err)
	}
	response.Body.Close()
	if attempts != 2 || response.StatusCode != http.StatusOK {
		t.Fatalf("attempts = %d, status = %d", attempts, response.StatusCode)
	}
}

func TestOriginAuthTransportDoesNotSendCredentialsToOtherHosts(t *testing.T) {
	transport, err := NewOriginAuthTransport(
		roundTripperFunc(func(request *http.Request) (*http.Response, error) {
			if request.Header.Get("Authorization") != "" {
				t.Fatal("credentials leaked to an unlisted host")
			}
			response := testResponse(request, http.StatusUnauthorized, "authenticate")
			response.Header.Set("WWW-Authenticate", `Basic realm="other"`)
			return response, nil
		}), map[string]Credentials{"example.test": {Username: "operator", Password: "secret"}},
	)
	if err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodGet, "https://other.test/private", nil)
	response, err := transport.RoundTrip(request)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	body, _ := io.ReadAll(response.Body)
	if response.StatusCode != http.StatusUnauthorized || string(body) != "authenticate" {
		t.Fatalf("response = %d %q", response.StatusCode, body)
	}
}

func TestParseAuthParametersRejectsMalformedInput(t *testing.T) {
	for _, value := range []string{`realm`, `realm="unterminated`, `realm=one, realm=two`} {
		if _, err := parseAuthParameters(value); err == nil {
			t.Fatalf("malformed parameters accepted: %q", value)
		}
	}
}
