package plugin

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	"github.com/owtf/owtf/internal/model"
)

func TestDNSWordlistLabels(t *testing.T) {
	directory := t.TempDir()
	spec := model.PluginInput{Name: "wordlist", Type: "wordlist", Format: "dns-labels", MaximumBytes: 65536, MaximumLines: 1000}
	for _, text := range []string{"", "\n", "www.example.test\n", "../outside\n", "*\n", "-flag\n", "bad-\n", " two\n", "$(id)\n", "`id`\n", "a;b\n", "a,b\n", "'a'\n", "\"a\"\n", "caf\u00e9\n", strings.Repeat("a", 64) + "\n"} {
		if err := os.WriteFile(filepath.Join(directory, "names.txt"), []byte(text), 0o600); err != nil {
			t.Fatal(err)
		}
		if _, err := copyWordlist(directory, "names.txt", t.TempDir(), spec); err == nil {
			t.Errorf("accepted invalid DNS labels %q", text)
		}
	}
	text := "www\r\nAPI-1\r\n" + strings.Repeat("a", 63) + "\n"
	if err := os.WriteFile(filepath.Join(directory, "names.txt"), []byte(text), 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := copyWordlist(directory, "names.txt", t.TempDir(), spec); err != nil {
		t.Fatal(err)
	}
}

func TestDNSInputsAndManifest(t *testing.T) {
	catalog, err := Load(os.DirFS("../../plugins"))
	if err != nil {
		t.Fatal(err)
	}
	entry, ok := catalog.Get("PTES-011-bruteforce")
	if !ok {
		t.Fatal("DNS plugin missing")
	}
	for _, value := range []any{"example.test:53", "192.0.2.53", "192.0.2.53:0", "[::]:53", "224.0.0.1:53", "255.255.255.255:53", "[::ffff:0.0.0.0]:53", "[fe80::1%eth0]:53", "[::ffff:192.0.2.53%eth0]:53", "192.0.2.53:53;id", true} {
		if _, err := entry.ResolveInputs(map[string]any{"wordlist": "names.txt", "resolver": value}); err == nil {
			t.Errorf("accepted resolver %#v", value)
		}
	}
	for _, value := range []string{"192.0.2.53:53", "[2001:db8::53]:5353"} {
		inputs, err := entry.ResolveInputs(map[string]any{"wordlist": "names.txt", "resolver": value})
		if err != nil || inputs["resolver"] != value || inputs["threads"] != int64(2) {
			t.Fatalf("unexpected DNS inputs: %+v, %v", inputs, err)
		}
	}
	args := entry.Manifest.Spec.Runtime.Container.Args
	for _, forbidden := range []string{"--wildcard", "--no-fqdn", "--no-error", "--quiet", "--pattern", "--discover-pattern"} {
		for _, arg := range args {
			if arg == forbidden {
				t.Errorf("DNS plugin disables safety with %s", arg)
			}
		}
	}
	if entry.Manifest.Spec.Runtime.Container.ErrorPrefix != "[ERROR]" {
		t.Fatal("DNS lookup errors must fail the task even if Gobuster exits zero")
	}
	if !reflect.DeepEqual(entry.Manifest.Spec.TargetKinds, []string{"hostname"}) {
		t.Fatal("DNS discovery must be restricted to hostname targets")
	}
}

func TestDNSInputSchemas(t *testing.T) {
	for _, spec := range []model.PluginInput{
		{Name: "names", Type: "string", Format: "dns-labels"},
		{Name: "names", Type: "wordlist", Format: "unknown", MaximumBytes: 10, MaximumLines: 1},
		{Name: "resolver", Type: "address", Default: "resolver.test:53"},
		{Name: "resolver", Type: "address", Choices: []string{"192.0.2.53:53"}},
	} {
		if _, err := validateInputs([]model.PluginInput{spec}); err == nil {
			t.Errorf("accepted invalid input schema %+v", spec)
		}
	}
}

func TestDecodeGobusterDNS(t *testing.T) {
	context := decodeContext{technique: "PTES-011", target: model.Target{Kind: "hostname", Value: "example.test"}}
	result, err := decodeGobusterDNS([]byte("www.example.test 192.0.2.10,2001:db8::10\nWWW.example.test. 192.0.2.10\napi.example.test 192.0.2.11\n"), context)
	if err != nil || len(result.Observations) != 2 || len(result.URLs) != 0 || len(result.Findings) != 0 {
		t.Fatalf("unexpected DNS result: %+v, %v", result, err)
	}
	var data struct {
		Hostname  string
		Addresses []string
	}
	if err := json.Unmarshal([]byte(result.Observations[1].Data), &data); err != nil {
		t.Fatal(err)
	}
	if data.Hostname != "www.example.test" || !reflect.DeepEqual(data.Addresses, []string{"192.0.2.10", "2001:db8::10"}) || result.Observations[1].TechniqueCode != "PTES-011" {
		t.Fatalf("unexpected DNS observation: %+v", result.Observations[1])
	}
	for _, text := range []string{"noise", "example.test 192.0.2.1", "www.notexample.test 192.0.2.1", "www.example.test.evil 192.0.2.1", "https://www.example.test 192.0.2.1", "www.example.test not-an-ip", "www.example.test 192.0.2.1,", "www.example.test fe80::1%eth0", "www.example.test 192.0.2.1 extra"} {
		if _, err := decodeGobusterDNS([]byte(text), context); err == nil {
			t.Errorf("accepted malformed DNS result %q", text)
		}
	}
	if result, err := decodeGobusterDNS(nil, context); err != nil || len(result.Observations) != 0 {
		t.Fatalf("empty DNS result: %+v, %v", result, err)
	}
}

func TestCapturedGobusterDNS(t *testing.T) {
	data, err := os.ReadFile("testdata/gobuster-dns.txt")
	if err != nil {
		t.Fatal(err)
	}
	result, err := decodeGobusterDNS(data, decodeContext{target: model.Target{Kind: "hostname", Value: "dns.owtf.test"}, technique: "PTES-011"})
	if err != nil || len(result.Observations) != 2 || len(result.Findings) != 0 || len(result.URLs) != 0 {
		t.Fatalf("captured DNS output failed: %+v, %v", result, err)
	}
}
