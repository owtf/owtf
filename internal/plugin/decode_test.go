package plugin

import (
	"strings"
	"testing"
	"testing/fstest"

	"github.com/owtf/owtf/internal/model"
)

func TestArtifactDecoders(t *testing.T) {
	context := decodeContext{
		technique: "OWTF-TEST-001",
		target:    model.Target{Kind: "url", Value: "https://example.test/base/"},
	}
	tests := []struct {
		name         string
		decoder      string
		data         string
		urls         int
		observations int
		findings     int
		severity     string
	}{
		{
			name: "testssl", decoder: "testssl-json",
			data:     `[{"id":"TLS1","severity":"HIGH","finding":"TLS 1.0 enabled","cwe":"CWE-326"},{"id":"TLS13","severity":"OK","finding":"TLS 1.3 enabled"}]`,
			findings: 1, observations: 1, severity: "high",
		},
		{
			name: "wafw00f", decoder: "wafw00f-json",
			data:         `[{"url":"https://example.test","detected":true,"firewall":"ExampleWAF","manufacturer":"Example"}]`,
			observations: 1,
		},
		{
			name: "whatweb", decoder: "whatweb-json",
			data: `[{"target":"https://example.test/","http_status":200,"plugins":{"nginx":{"version":["1.2"]}}}]`,
			urls: 1, observations: 1,
		},
		{
			name: "nuclei", decoder: "nuclei-jsonl",
			data: `{"template-id":"takeover","matched-at":"https://sub.example.test/","info":{"name":"Dangling service","severity":"critical","description":"service can be claimed"}}`,
			urls: 1, findings: 1, severity: "critical",
		},
		{
			name: "wapiti", decoder: "wapiti-json",
			data: `{"vulnerabilities":{"XSS":[{"method":"GET","path":"/search","info":"reflected input","level":3,"parameter":"q"}]},` +
				`"anomalies":{"Timeout":[{"method":"GET","path":"/slow","info":"timed out","level":1}]}}`,
			urls: 1, observations: 1, findings: 1, severity: "high",
		},
		{
			name: "metagoofil", decoder: "url-list",
			data: "https://example.test/one.pdf\nnot-a-url\nhttps://cdn.example.test/two.doc\n",
			urls: 2, observations: 1,
		},
		{
			name: "gobuster dir", decoder: "gobuster-dir",
			data: "/admin (Status: 200) [Size: 12]\nnoise\n",
			urls: 1, observations: 1,
		},
		{
			name: "gobuster dir 3.8", decoder: "gobuster-dir",
			data: "admin           (Status: 301) [Size: 12] [--> /admin/]\nnoise\n",
			urls: 1, observations: 1,
		},
		{
			name: "gobuster vhost", decoder: "gobuster-vhost",
			data: "Found: api.example.test Status: 200 [Size: 12]\n",
			urls: 1, observations: 1,
		},
		{
			name: "gobuster vhost 3.8", decoder: "gobuster-vhost",
			data: "admin.example.test:8080 Status: 200 [Size: 26]\n",
			urls: 1, observations: 1,
		},
		{
			name: "gobuster gcs", decoder: "gobuster-gcs",
			data:         "Found: public-example [Status: 200]\n",
			observations: 1,
		},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			result, err := artifactDecoders[test.decoder]([]byte(test.data), context)
			if err != nil {
				t.Fatal(err)
			}
			if len(result.URLs) != test.urls || len(result.Observations) != test.observations || len(result.Findings) != test.findings {
				t.Fatalf("unexpected result: %+v", result)
			}
			if test.severity != "" && result.Findings[0].Severity != test.severity {
				t.Fatalf("severity = %q", result.Findings[0].Severity)
			}
		})
	}
}

func TestGobusterVHostPreservesPort(t *testing.T) {
	context := decodeContext{target: model.Target{Kind: "url", Value: "http://example.test:8080/"}}
	result, err := decodeGobusterVHost([]byte("admin.example.test:8080 Status: 200 [Size: 26]\n"), context)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.URLs) != 1 || result.URLs[0].URL != "http://admin.example.test:8080" || !result.URLs[0].Visited {
		t.Fatalf("virtual-host URL lost its scheme or port: %+v", result.URLs)
	}
}

func TestArtifactDecodersRejectMalformedOutput(t *testing.T) {
	context := decodeContext{technique: "OWTF-TEST-001", target: model.Target{Kind: "url", Value: "https://example.test/"}}
	for name, test := range map[string]struct {
		decoder string
		data    string
	}{
		"invalid json":       {"testssl-json", `{`},
		"incomplete testssl": {"testssl-json", `[{"id":"test"}]`},
		"invalid jsonl":      {"nuclei-jsonl", `{`},
		"incomplete nuclei":  {"nuclei-jsonl", `{}`},
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := artifactDecoders[test.decoder]([]byte(test.data), context); err == nil {
				t.Fatal("malformed scanner output was accepted")
			}
		})
	}
}

func TestManifestRejectsUnknownArtifactDecoder(t *testing.T) {
	manifest := commandManifest(`executable: echo
      artifacts:
        - name: report.json
          decoder: arbitrary-code`, "")
	_, err := Load(fstest.MapFS{"plugin.yaml": {Data: []byte(manifest)}})
	if err == nil || !strings.Contains(err.Error(), "unsupported artifact decoder") {
		t.Fatalf("unexpected error: %v", err)
	}
}
