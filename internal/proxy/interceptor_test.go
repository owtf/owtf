package proxy

import (
	"context"
	"errors"
	"io"
	"net/http"
	"strings"
	"sync"
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
	for name, input := range map[string]string{
		"unknown field": `{"rules":[{"name":"bad","phase":"request","action":{},"unknown":true}]}`,
		"null":          `null`,
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := LoadInterceptors(strings.NewReader(input), 1024); err == nil {
				t.Fatal("invalid interceptor document was accepted")
			}
		})
	}
}

func TestInterceptorsReplaceAndSetEnabled(t *testing.T) {
	rules := []InterceptorRule{{
		Name: "header", Phase: "request",
		Action: InterceptorAction{SetHeaders: map[string]string{"X-OWTF": "initial"}},
	}}
	interceptors, err := NewInterceptors(rules, 1024)
	if err != nil {
		t.Fatal(err)
	}
	rules[0].Action.SetHeaders["X-OWTF"] = "mutated"
	config := interceptors.Config()
	config.Rules[0].Action.SetHeaders["X-OWTF"] = "also-mutated"
	if got := interceptors.Config().Rules[0].Action.SetHeaders["X-OWTF"]; got != "initial" {
		t.Fatalf("active interceptor aliased caller state: %q", got)
	}

	if err := interceptors.Replace([]InterceptorRule{{Name: "broken", Phase: "request", Match: InterceptorMatch{URLPattern: "["}}}); err == nil {
		t.Fatal("invalid replacement was accepted")
	}
	request, _ := http.NewRequest(http.MethodGet, "https://example.test", nil)
	if err := interceptors.InterceptRequest(context.Background(), request); err != nil || request.Header.Get("X-OWTF") != "initial" {
		t.Fatalf("failed replacement changed active rules: header=%q err=%v", request.Header.Get("X-OWTF"), err)
	}

	rule, err := interceptors.SetEnabled("header", false)
	if err != nil || rule.Enabled == nil || *rule.Enabled {
		t.Fatalf("disabled rule = %+v, error = %v", rule, err)
	}
	request, _ = http.NewRequest(http.MethodGet, "https://example.test", nil)
	if err := interceptors.InterceptRequest(context.Background(), request); err != nil || request.Header.Get("X-OWTF") != "" {
		t.Fatalf("disabled interceptor applied: header=%q err=%v", request.Header.Get("X-OWTF"), err)
	}
	if _, err := interceptors.SetEnabled("missing", true); !errors.Is(err, ErrInterceptorNotFound) {
		t.Fatalf("missing rule error = %v", err)
	}
}

func TestInterceptorsReplaceWhileMatching(t *testing.T) {
	ruleSet := func(generation string) []InterceptorRule {
		return []InterceptorRule{
			{Name: "first", Priority: 1, Phase: "request", Action: InterceptorAction{SetHeaders: map[string]string{"X-First": generation}}},
			{Name: "second", Priority: 2, Phase: "request", Action: InterceptorAction{SetHeaders: map[string]string{"X-Second": generation}}},
		}
	}
	interceptors, err := NewInterceptors(ruleSet("a"), 1024)
	if err != nil {
		t.Fatal(err)
	}
	failures := make(chan string, 2)
	var group sync.WaitGroup
	group.Add(2)
	go func() {
		defer group.Done()
		for index := range 1000 {
			generation := "a"
			if index%2 == 0 {
				generation = "b"
			}
			if err := interceptors.Replace(ruleSet(generation)); err != nil {
				failures <- err.Error()
				return
			}
		}
	}()
	go func() {
		defer group.Done()
		for range 1000 {
			request, _ := http.NewRequest(http.MethodGet, "https://example.test", nil)
			if err := interceptors.InterceptRequest(context.Background(), request); err != nil {
				failures <- err.Error()
				return
			}
			if first, second := request.Header.Get("X-First"), request.Header.Get("X-Second"); first == "" || first != second {
				failures <- "one request observed two interceptor generations"
				return
			}
		}
	}()
	group.Wait()
	select {
	case failure := <-failures:
		t.Fatal(failure)
	default:
	}
}
