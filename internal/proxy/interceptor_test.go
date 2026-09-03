package proxy

import (
	"context"
	"io"
	"net/http"
	"strings"
	"testing"
)

func TestInterceptorsApplyRequestRulesInPriorityOrder(t *testing.T) {
	interceptors, err := NewInterceptors([]InterceptorRule{
		{
			Name: "append", Priority: 20, Phase: "request",
			Match:  InterceptorMatch{URLPattern: `example\.test`, Methods: []string{"post"}, ContentTypes: []string{"json"}},
			Action: InterceptorAction{AddHeaders: map[string]string{"X-Order": "second"}, BodyAppend: `}`},
		},
		{
			Name: "rewrite", Priority: 10, Phase: "request",
			Action: InterceptorAction{
				SetHeaders: map[string]string{"X-Test": "set"}, RemoveHeaders: []string{"X-Remove"},
				BodyPrepend: `{`, RewriteURL: &TextReplacement{Pattern: `/old`, Replacement: `/new`},
			},
		},
	}, 1024)
	if err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodPost, "https://example.test/old", strings.NewReader(`"ok":true`))
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("X-Remove", "yes")
	if err := interceptors.InterceptRequest(context.Background(), request); err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(request.Body)
	if request.URL.Path != "/new" || request.Host != "example.test" {
		t.Fatalf("rewritten URL = %s, host = %s", request.URL, request.Host)
	}
	if string(body) != `{"ok":true}` || request.ContentLength != int64(len(body)) {
		t.Fatalf("body = %q, length = %d", body, request.ContentLength)
	}
	if request.Header.Get("X-Test") != "set" || request.Header.Get("X-Remove") != "" || request.Header.Get("X-Order") != "second" {
		t.Fatalf("headers = %v", request.Header)
	}
}

func TestInterceptorsModifyResponseAndRepairEntityHeaders(t *testing.T) {
	interceptors, err := NewInterceptors([]InterceptorRule{{
		Name: "response", Phase: "response", Match: InterceptorMatch{ContentTypes: []string{"text/plain"}},
		Action: InterceptorAction{
			BodyReplace: []TextReplacement{{Pattern: "secret", Replacement: "redacted"}},
			SetHeaders:  map[string]string{"X-Reviewed": "true"},
		},
	}}, 1024)
	if err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodGet, "https://example.test", nil)
	response := testResponse(request, http.StatusOK, "secret")
	response.Header.Set("Content-Type", "text/plain")
	response.Header.Set("ETag", "old")
	if err := interceptors.InterceptResponse(context.Background(), response); err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(response.Body)
	response.Body.Close()
	if string(body) != "redacted" || response.ContentLength != 8 || response.Header.Get("Content-Length") != "8" {
		t.Fatalf("body = %q, content length = %d, header = %q", body, response.ContentLength, response.Header.Get("Content-Length"))
	}
	if response.Header.Get("ETag") != "" || response.Header.Get("X-Reviewed") != "true" {
		t.Fatalf("headers = %v", response.Header)
	}
}

func TestInterceptorsRejectUnsafeOrUnboundedRules(t *testing.T) {
	for name, rule := range map[string]InterceptorRule{
		"header injection": {Name: "bad", Phase: "request", Action: InterceptorAction{SetHeaders: map[string]string{"X-Test": "one\r\ntwo"}}},
		"bad regexp":       {Name: "bad", Phase: "request", Action: InterceptorAction{RewriteURL: &TextReplacement{Pattern: "[", Replacement: ""}}},
		"long delay":       {Name: "bad", Phase: "request", Action: InterceptorAction{DelayMS: 60_001}},
		"encoded body": {
			Name: "bad", Phase: "response",
			Action: InterceptorAction{BodyAppend: "x", SetHeaders: map[string]string{"content-encoding": "gzip"}},
		},
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := NewInterceptors([]InterceptorRule{rule}, 1024); err == nil {
				t.Fatal("unsafe interceptor rule was accepted")
			}
		})
	}
}

func TestInterceptorsNormalizeNamesBeforeDuplicateCheck(t *testing.T) {
	_, err := NewInterceptors([]InterceptorRule{
		{Name: "same", Phase: "request"},
		{Name: " same ", Phase: "response"},
	}, 1024)
	if err == nil {
		t.Fatal("duplicate normalized names were accepted")
	}
}

func TestInterceptorsDoNotModifyOriginallyEncodedBodies(t *testing.T) {
	interceptors, err := NewInterceptors([]InterceptorRule{
		{Name: "remove encoding", Priority: 1, Phase: "response", Action: InterceptorAction{RemoveHeaders: []string{"Content-Encoding"}}},
		{Name: "body", Priority: 2, Phase: "response", Action: InterceptorAction{BodyAppend: "x"}},
	}, 1024)
	if err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodGet, "https://example.test", nil)
	response := testResponse(request, http.StatusOK, "compressed")
	response.Header.Set("Content-Encoding", "gzip")
	if err := interceptors.InterceptResponse(context.Background(), response); err == nil {
		t.Fatal("body rule modified originally encoded content")
	}
}

func TestInterceptorsDoNotModifyBodiesEncodedByEarlierRule(t *testing.T) {
	interceptors, err := NewInterceptors([]InterceptorRule{
		{Name: "add encoding", Priority: 1, Phase: "request", Action: InterceptorAction{SetHeaders: map[string]string{"Content-Encoding": "gzip"}}},
		{Name: "body", Priority: 2, Phase: "request", Action: InterceptorAction{BodyAppend: "x"}},
	}, 1024)
	if err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodPost, "https://example.test", strings.NewReader("plain"))
	if err := interceptors.InterceptRequest(context.Background(), request); err == nil {
		t.Fatal("body rule modified content marked encoded by an earlier rule")
	}
}

func TestInterceptorsRejectOversizedBody(t *testing.T) {
	interceptors, err := NewInterceptors([]InterceptorRule{{
		Name: "body", Phase: "request", Action: InterceptorAction{BodyAppend: "x"},
	}}, 4)
	if err != nil {
		t.Fatal(err)
	}
	request, _ := http.NewRequest(http.MethodPost, "https://example.test", strings.NewReader("12345"))
	if err := interceptors.InterceptRequest(context.Background(), request); err == nil {
		t.Fatal("oversized body was accepted")
	}
}

func TestLoadInterceptorsRejectsUnknownFields(t *testing.T) {
	_, err := LoadInterceptors(strings.NewReader(`{"rules":[{"name":"bad","phase":"request","action":{},"unknown":true}]}`), 1024)
	if err == nil {
		t.Fatal("unknown interceptor field was accepted")
	}
}
