package plugin

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/owtf/owtf/internal/model"
)

func TestNmapCapturedXML(t *testing.T) {
	for _, test := range []struct {
		file  string
		port  int
		state string
	}{
		{"nmap-ftp.xml", 21, "open"},
		{"nmap-closed.xml", 65000, "closed"},
	} {
		t.Run(test.file, func(t *testing.T) {
			result, err := decodeNmap(scannerXML(t, test.file), decodeContext{technique: "PTES-001"})
			if err != nil {
				t.Fatal(err)
			}
			if len(result.Findings) != 0 {
				t.Fatal("Nmap evidence was incorrectly promoted to vulnerabilities")
			}
			ports, scripts := 0, 0
			for _, item := range result.Observations {
				if item.TechniqueCode != "PTES-001" {
					t.Fatalf("lost technique: %+v", item)
				}
				var record struct {
					Port    int
					State   string
					Service *nmapService
					ID      string
					Output  string
				}
				if err := json.Unmarshal([]byte(item.Data), &record); err != nil {
					t.Fatal(err)
				}
				switch item.Kind {
				case "network.port":
					ports++
					if record.Port != test.port || record.State != test.state {
						t.Fatalf("wrong port: %s", item.Data)
					}
					if test.state == "open" && (record.Service == nil || record.Service.Name != "ftp" || record.Service.Product != "vsftpd" || record.Service.Version != "3.0.5" || len(record.Service.CPEs) != 1) {
						t.Fatalf("missing service fingerprint: %s", item.Data)
					}
				case "network.script":
					scripts++
					if record.ID == "ftp-anon" && !strings.Contains(record.Output, "Anonymous FTP login allowed") {
						t.Fatalf("lost NSE output: %s", item.Data)
					}
				}
			}
			if ports != 1 || (test.state == "open" && scripts != 2) || (test.state == "closed" && scripts != 0) {
				t.Fatalf("unexpected port/script counts: %d/%d", ports, scripts)
			}
		})
	}
}

func TestNiktoCapturedXML(t *testing.T) {
	context := decodeContext{technique: "OWTF-WVS-002", target: model.Target{Kind: "url", Value: "https://example.test:8443/base/"}}
	result, err := decodeNikto(scannerXML(t, "nikto.xml"), context)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Findings) != 8 || len(result.URLs) != 8 {
		t.Fatalf("Nikto items (including repeated IDs) were lost: %+v", result)
	}
	admin := false
	for _, item := range result.Findings {
		if item.Severity != "unranked" || item.TechniqueCode != context.technique || !strings.Contains(item.Description, "GET") {
			t.Fatalf("unexpected finding: %+v", item)
		}
		if strings.Contains(item.Description, "https://example.test:8443/admin/index.html") {
			admin = true
		}
	}
	if !admin {
		t.Fatal("missing affected URL in finding")
	}
	for _, item := range result.URLs {
		if !strings.HasPrefix(item.URL, "https://example.test:8443/") || !item.Visited {
			t.Fatalf("URI lost target scheme/port: %+v", item)
		}
	}
}

func TestNmapCapturedSMTPAndSMB(t *testing.T) {
	for _, test := range []struct {
		file      string
		technique string
		port      int
		product   string
		scripts   map[string][]string
	}{
		{"nmap-smtp.xml", "PTES-002", 25, "Postfix smtpd", map[string][]string{
			"smtp-commands": {"smtp.owtf.test", "PIPELINING", "SIZE"},
		}},
		{"nmap-smb-required.xml", "PTES-009", 445, "Samba smbd", map[string][]string{
			"smb-protocols":      {"2.0.2", "3.1.1"},
			"smb2-capabilities":  {"Multi-credit operations"},
			"smb2-security-mode": {"Message signing enabled and required"},
		}},
		{"nmap-smb-optional.xml", "PTES-009", 445, "Samba smbd", map[string][]string{
			"smb-protocols":      {"2.0.2", "3.1.1"},
			"smb2-capabilities":  {"Multi-credit operations"},
			"smb2-security-mode": {"Message signing enabled but not required"},
		}},
	} {
		t.Run(test.file, func(t *testing.T) {
			result, err := decodeNmap(scannerXML(t, test.file), decodeContext{technique: test.technique})
			if err != nil {
				t.Fatal(err)
			}
			if len(result.Findings) != 0 || len(result.Observations) != len(test.scripts)+2 {
				t.Fatalf("unexpected findings or observations: %+v", result)
			}
			ports := 0
			scripts := make(map[string]string)
			for _, item := range result.Observations {
				var record struct {
					Port    int
					State   string
					Service *nmapService
					ID      string
					Output  string
				}
				if err := json.Unmarshal([]byte(item.Data), &record); err != nil || item.TechniqueCode != test.technique {
					t.Fatalf("invalid observation: %+v, %v", item, err)
				}
				switch item.Kind {
				case "network.port":
					ports++
					if record.Port != test.port || record.State != "open" || record.Service == nil || record.Service.Product != test.product {
						t.Fatalf("missing service evidence: %s", item.Data)
					}
				case "network.script":
					scripts[record.ID] = record.Output
				}
			}
			if ports != 1 || len(scripts) != len(test.scripts) {
				t.Fatalf("unexpected port/script counts: %d/%d", ports, len(scripts))
			}
			for id, markers := range test.scripts {
				for _, marker := range markers {
					if !strings.Contains(scripts[id], marker) {
						t.Errorf("%s lost %q: %q", id, marker, scripts[id])
					}
				}
			}
		})
	}
}

func TestNmapHostScriptsAndPortSummary(t *testing.T) {
	data := nmapDocument(`<host><status state="up"/><address addr="::1" addrtype="ipv6"/><ports><extraports state="filtered" count="10"/></ports><hostscript><script id="smb-protocols" output="SMBv2&#xa;SMBv3"/></hostscript></host>`)
	result, err := decodeNmap([]byte(data), decodeContext{})
	if err != nil || len(result.Observations) != 3 || len(result.Findings) != 0 {
		t.Fatalf("host script/summary: %+v, %v", result, err)
	}
	if result.Observations[2].Kind != "network.script" || !strings.Contains(result.Observations[2].Data, "SMBv2\\nSMBv3") {
		t.Fatalf("host script lost multiline output: %+v", result)
	}
}

func TestXMLDecodersEmptyReports(t *testing.T) {
	for name, data := range map[string]string{
		"nmap-xml":  nmapDocument(""),
		"nikto-xml": niktoDocument(""),
	} {
		result, err := artifactDecoders[name]([]byte(data), decodeContext{})
		if err != nil || len(result.Findings)+len(result.Observations)+len(result.URLs) != 0 {
			t.Fatalf("empty %s report: %+v, %v", name, result, err)
		}
	}
}

func TestNiktoSeverityAndUnsafeURI(t *testing.T) {
	data := niktoDocument(`<item id="1" severity="HIGH"><description><![CDATA[<script>alert(1)</script>]]></description><uri>javascript:alert(1)</uri></item><item id="2" severity="unknown"><description>Other check</description></item>`)
	result, err := decodeNikto([]byte(data), decodeContext{target: model.Target{Value: "https://example.test"}})
	if err != nil || len(result.Findings) != 2 || len(result.URLs) != 0 {
		t.Fatalf("result: %+v, %v", result, err)
	}
	if result.Findings[0].Severity != "high" || result.Findings[1].Severity != "unranked" {
		t.Fatalf("incorrect severity handling: %+v", result.Findings)
	}
}

func TestXMLDecodersRejectMalformedReports(t *testing.T) {
	for _, decoder := range []string{"nmap-xml", "nikto-xml"} {
		valid := nmapDocument("")
		if decoder == "nikto-xml" {
			valid = niktoDocument("")
		}
		for name, data := range map[string]string{
			"empty": "", "wrong root": "<other/>", "truncated": valid[:len(valid)-4],
			"multiple roots": valid + valid, "trailing garbage": valid + "garbage",
			"prefix garbage":   "garbage" + valid,
			"oversized":        strings.Repeat(" ", maxArtifactSize+1),
			"external entity":  `<!DOCTYPE nmaprun [<!ENTITY file SYSTEM "file:///etc/passwd">]>` + valid,
			"entity expansion": `<!DOCTYPE nmaprun [<!ENTITY a "boom"><!ENTITY b "&a;&a;">]>` + valid,
			"depth":            strings.Replace(valid, "></", ">"+strings.Repeat("<x>", maxXMLDepth)+strings.Repeat("</x>", maxXMLDepth)+"</", 1),
		} {
			t.Run(decoder+"/"+name, func(t *testing.T) {
				if result, err := artifactDecoders[decoder]([]byte(data), decodeContext{}); err == nil || len(result.Observations)+len(result.Findings) != 0 {
					t.Fatalf("invalid report accepted: %+v, %v", result, err)
				}
			})
		}
	}
	for name, test := range map[string]struct{ decoder, data string }{
		"Nmap unfinished":           {"nmap-xml", "<nmaprun/>"},
		"Nmap failed":               {"nmap-xml", `<nmaprun><runstats><finished exit="error"/></runstats></nmaprun>`},
		"Nmap missing address":      {"nmap-xml", nmapDocument(`<host><status state="up"/></host>`)},
		"Nmap invalid port":         {"nmap-xml", nmapDocument(`<host><status state="up"/><address addr="::1" addrtype="ipv6"/><ports><port portid="65536" protocol="tcp"><state state="open"/></port></ports></host>`)},
		"Nikto missing scan":        {"nikto-xml", "<niktoscans/>"},
		"Nikto missing details":     {"nikto-xml", "<niktoscans><niktoscan/></niktoscans>"},
		"Nikto missing description": {"nikto-xml", niktoDocument(`<item id="1"/>`)},
		"Nikto unknown entity":      {"nikto-xml", niktoDocument(`<item><description>&unknown;</description></item>`)},
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := artifactDecoders[test.decoder]([]byte(test.data), decodeContext{}); err == nil {
				t.Fatal("incomplete report accepted")
			}
		})
	}
}

func TestXMLDecodersRecordLimits(t *testing.T) {
	for name, data := range map[string]string{
		"nmap-xml":  nmapDocument(`<host><status state="up"/><address addr="::1" addrtype="ipv6"/><hostscript>` + strings.Repeat(`<script id="test" output="output"/>`, maxDecodedRecords+1) + `</hostscript></host>`),
		"nikto-xml": niktoDocument(strings.Repeat(`<item><description>Finding</description></item>`, maxDecodedRecords+1)),
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := artifactDecoders[name]([]byte(data), decodeContext{}); err == nil || !strings.Contains(err.Error(), "records") {
				t.Fatalf("record limit not enforced: %v", err)
			}
		})
	}
}

func TestNmapTextIsBounded(t *testing.T) {
	data := nmapDocument(fmt.Sprintf(`<host><status state="up"/><address addr="::1" addrtype="ipv6"/><hostscript><script id="test" output="%s"/></hostscript></host>`, strings.Repeat("x", maxDecodedText+1)))
	result, err := decodeNmap([]byte(data), decodeContext{})
	if err != nil {
		t.Fatal(err)
	}
	var record struct{ Output string }
	if err := json.Unmarshal([]byte(result.Observations[1].Data), &record); err != nil || len(record.Output) != maxDecodedText {
		t.Fatalf("unbounded script output: %d, %v", len(record.Output), err)
	}
}

func scannerXML(t *testing.T, name string) []byte {
	t.Helper()
	data, err := os.ReadFile(filepath.Join("testdata", "xml", name))
	if err != nil {
		t.Fatal(err)
	}
	return data
}

func nmapDocument(hosts string) string {
	return "<nmaprun>" + hosts + `<runstats><finished exit="success"/></runstats></nmaprun>`
}

func niktoDocument(items string) string {
	return "<niktoscans><niktoscan><scandetails>" + items + "</scandetails></niktoscan></niktoscans>"
}
