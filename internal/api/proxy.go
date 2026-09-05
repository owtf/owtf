package api

import (
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// proxyAPI exposes only the known control API of the configured local proxy.
// It is not a general-purpose reverse proxy and never forwards browser cookies.
func proxyAPI(address string) http.Handler {
	client := &http.Client{
		Timeout:       90 * time.Second,
		Transport:     &http.Transport{Proxy: nil, DialContext: (&net.Dialer{Timeout: 3 * time.Second}).DialContext, ResponseHeaderTimeout: 85 * time.Second},
		CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse },
	}
	host, port, err := net.SplitHostPort(address)
	ip := net.ParseIP(host)
	valid := err == nil && ip != nil && ip.IsLoopback() && port != "0"
	forward := func(w http.ResponseWriter, r *http.Request) {
		if !valid {
			writeError(w, http.StatusServiceUnavailable, "configure a loopback proxy.apiAddress and start owtf proxy")
			return
		}
		if r.Method != http.MethodGet {
			origin, err := url.Parse(r.Header.Get("Origin"))
			if r.Header.Get("Sec-Fetch-Site") == "cross-site" || (r.Header.Get("Origin") != "" && (err != nil || origin.Host != r.Host)) {
				writeError(w, http.StatusForbidden, "cross-site proxy commands are not allowed")
				return
			}
		}
		path := strings.TrimPrefix(r.URL.Path, "/api/v2/proxy")
		upstream := url.URL{Scheme: "http", Host: address, Path: "/api/v2" + path, RawQuery: r.URL.RawQuery}
		body := http.MaxBytesReader(w, r.Body, 16<<20)
		request, err := http.NewRequestWithContext(r.Context(), r.Method, upstream.String(), body)
		if err != nil {
			writeError(w, http.StatusBadRequest, "invalid proxy command")
			return
		}
		request.Header.Set("Content-Type", r.Header.Get("Content-Type"))
		response, err := client.Do(request)
		if err != nil {
			writeError(w, http.StatusBadGateway, "proxy API unavailable; check the proxy process before repeating a command")
			return
		}
		defer response.Body.Close()
		// Bound responses before committing headers; never return truncated JSON.
		data, err := io.ReadAll(io.LimitReader(response.Body, (64<<20)+1))
		if err != nil || len(data) > 64<<20 {
			writeError(w, http.StatusBadGateway, "proxy response incomplete or too large")
			return
		}
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("Content-Type", response.Header.Get("Content-Type"))
		w.Header().Set("Content-Disposition", response.Header.Get("Content-Disposition"))
		w.WriteHeader(response.StatusCode)
		_, _ = w.Write(data)
	}
	mux := http.NewServeMux()
	for _, route := range []string{
		"GET /capture", "PUT /capture",
		"GET /health", "GET /ca", "GET /transactions", "DELETE /transactions",
		"GET /transactions/stats", "GET /transactions/{id}", "POST /repeater",
		"GET /interceptors", "PUT /interceptors", "PATCH /interceptors",
		"GET /interception", "PUT /interception", "GET /interception/pending",
		"GET /interception/pending/{id}", "POST /interception/pending/{id}/continue",
		"POST /interception/pending/{id}/drop",
	} {
		method, path, _ := strings.Cut(route, " ")
		mux.HandleFunc(method+" /api/v2/proxy"+path, forward)
	}
	return mux
}
