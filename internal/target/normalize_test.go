package target

import "testing"

func TestNormalize(t *testing.T) {
	tests := []struct {
		input string
		kind  string
		value string
	}{
		{" HTTPS://Example.COM:443/path#fragment ", "url", "https://example.com/path"},
		{"example.com", "hostname", "example.com"},
		{"127.0.0.1", "ip", "127.0.0.1"},
		{"10.0.0.0/24", "cidr", "10.0.0.0/24"},
	}
	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got, err := Normalize(tt.input)
			if err != nil {
				t.Fatalf("Normalize() error = %v", err)
			}
			if got.Kind != tt.kind || got.Value != tt.value {
				t.Fatalf("Normalize() = %#v, want kind=%q value=%q", got, tt.kind, tt.value)
			}
		})
	}
}

func TestNormalizeRejectsUnsafeURL(t *testing.T) {
	for _, input := range []string{"", "file:///etc/passwd", "https://user:pass@example.com", "not a host!"} {
		if _, err := Normalize(input); err == nil {
			t.Fatalf("Normalize(%q) unexpectedly succeeded", input)
		}
	}
}

func TestNormalizeURLAndScope(t *testing.T) {
	canonical, err := NormalizeURL(" HTTPS://Example.COM:443/path#fragment ")
	if err != nil || canonical != "https://example.com/path" {
		t.Fatalf("NormalizeURL() = %q, %v", canonical, err)
	}
	canonical, err = NormalizeURL("https://Example.COM./path")
	if err != nil || canonical != "https://example.com/path" {
		t.Fatalf("NormalizeURL() trailing dot = %q, %v", canonical, err)
	}
	tests := []struct {
		kind      string
		target    string
		candidate string
		want      bool
	}{
		{"url", "https://example.com/root", "http://example.com/child", true},
		{"url", "https://example.com/root", "https://cdn.example.com/child", false},
		{"hostname", "example.com", "https://example.com:8443/", true},
		{"hostname", "example.com", "https://sub.example.com/", false},
		{"ip", "192.0.2.4", "https://192.0.2.4/", true},
		{"cidr", "192.0.2.0/28", "http://192.0.2.14/", true},
		{"cidr", "192.0.2.0/28", "http://192.0.2.16/", false},
		{"hostname", "example.com", "ftp://example.com/", false},
		{"unknown", "example.com", "https://example.com/", false},
	}
	for _, test := range tests {
		if got := URLInScope(test.kind, test.target, test.candidate); got != test.want {
			t.Errorf("URLInScope(%q, %q, %q) = %t, want %t", test.kind, test.target, test.candidate, got, test.want)
		}
	}
}
