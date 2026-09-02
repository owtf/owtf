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
