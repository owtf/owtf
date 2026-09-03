package plugin

import (
	"bytes"
	"encoding/xml"
	"errors"
	"fmt"
	"io"
	"strconv"
	"strings"
)

const maxXMLDepth = 32

// decodeXML checks the entire document before allocating scanner records.
// encoding/xml never fetches external DTDs or stylesheets. Internal DTD subsets
// are rejected, and the default entity map is left unchanged.
func decodeXML(data []byte, root string, out any) error {
	if len(data) > maxArtifactSize {
		return fmt.Errorf("XML report exceeds %d bytes", maxArtifactSize)
	}
	d := xml.NewDecoder(bytes.NewReader(data))
	depth, elements, roots := 0, 0, 0
	for {
		token, err := d.Token()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}
		switch token := token.(type) {
		case xml.StartElement:
			if depth == 0 {
				roots++
				if roots != 1 || token.Name != (xml.Name{Local: root}) {
					return fmt.Errorf("expected one %s XML document", root)
				}
			}
			depth++
			elements++
			if depth > maxXMLDepth || elements > maxDecodedRecords*16 {
				return errors.New("XML report exceeds nesting or element limit")
			}
		case xml.EndElement:
			depth--
		case xml.CharData:
			if depth == 0 && len(bytes.TrimSpace(token)) != 0 {
				return errors.New("unexpected text outside XML root")
			}
		case xml.Directive:
			if roots != 0 || !bytes.HasPrefix(token, []byte("DOCTYPE ")) || bytes.ContainsAny(token, "[]") {
				return errors.New("unsupported XML directive or internal DTD subset")
			}
		}
	}
	if roots != 1 {
		return fmt.Errorf("missing %s XML document", root)
	}
	return xml.Unmarshal(data, out)
}

type nmapService struct {
	Name    string   `xml:"name,attr" json:"name"`
	Product string   `xml:"product,attr" json:"product,omitempty"`
	Version string   `xml:"version,attr" json:"version,omitempty"`
	Extra   string   `xml:"extrainfo,attr" json:"extra,omitempty"`
	Tunnel  string   `xml:"tunnel,attr" json:"tunnel,omitempty"`
	OS      string   `xml:"ostype,attr" json:"os,omitempty"`
	CPEs    []string `xml:"cpe" json:"cpes,omitempty"`
}

type nmapScript struct {
	ID     string `xml:"id,attr"`
	Output string `xml:"output,attr"`
}

type nmapState struct {
	State  string `xml:"state,attr"`
	Reason string `xml:"reason,attr"`
}

func decodeNmap(data []byte, context decodeContext) (Result, error) {
	var report struct {
		Hosts []struct {
			Status    nmapState `xml:"status"`
			Addresses []struct {
				Address string `xml:"addr,attr"`
				Type    string `xml:"addrtype,attr"`
			} `xml:"address"`
			Ports []struct {
				Port     string       `xml:"portid,attr"`
				Protocol string       `xml:"protocol,attr"`
				State    nmapState    `xml:"state"`
				Service  *nmapService `xml:"service"`
				Scripts  []nmapScript `xml:"script"`
			} `xml:"ports>port"`
			ExtraPorts []struct {
				State string `xml:"state,attr"`
				Count int    `xml:"count,attr"`
			} `xml:"ports>extraports"`
			Scripts []nmapScript `xml:"hostscript>script"`
		} `xml:"host"`
		Finished struct {
			Exit string `xml:"exit,attr"`
		} `xml:"runstats>finished"`
	}
	if err := decodeXML(data, "nmaprun", &report); err != nil {
		return Result{}, err
	}
	if report.Finished.Exit != "success" {
		return Result{}, errors.New("Nmap report has no successful completion record")
	}
	var result Result
	appendScript := func(address, protocol string, port int, script nmapScript) error {
		if script.ID == "" {
			return errors.New("Nmap script is missing its id")
		}
		result.Observations = append(result.Observations, observation(context, "network.script", map[string]any{
			"address": address, "protocol": limited(protocol), "port": port,
			"id": limited(script.ID), "output": limited(script.Output),
		}))
		return nil
	}
	for _, host := range report.Hosts {
		address := ""
		for _, item := range host.Addresses {
			if item.Type == "ipv4" || item.Type == "ipv6" {
				address = limited(item.Address)
				break
			}
		}
		if address == "" || host.Status.State == "" {
			return Result{}, errors.New("Nmap host is missing address or status")
		}
		result.Observations = append(result.Observations, observation(context, "network.host", map[string]any{
			"address": address, "state": limited(host.Status.State), "reason": limited(host.Status.Reason),
		}))
		for _, port := range host.Ports {
			portNumber, err := strconv.Atoi(port.Port)
			if err != nil || portNumber < 0 || portNumber > 65535 || port.Protocol == "" || port.State.State == "" {
				return Result{}, errors.New("Nmap port is missing or has invalid port, protocol, or state")
			}
			if service := port.Service; service != nil {
				service.Name, service.Product, service.Version = limited(service.Name), limited(service.Product), limited(service.Version)
				service.Extra, service.Tunnel, service.OS = limited(service.Extra), limited(service.Tunnel), limited(service.OS)
				for i := range service.CPEs {
					service.CPEs[i] = limited(service.CPEs[i])
				}
			}
			result.Observations = append(result.Observations, observation(context, "network.port", map[string]any{
				"address": address, "port": portNumber, "protocol": limited(port.Protocol),
				"state": limited(port.State.State), "reason": limited(port.State.Reason), "service": port.Service,
			}))
			for _, script := range port.Scripts {
				if err := appendScript(address, port.Protocol, portNumber, script); err != nil {
					return Result{}, err
				}
			}
		}
		for _, ports := range host.ExtraPorts {
			if ports.State == "" || ports.Count < 1 {
				return Result{}, errors.New("Nmap port summary is missing state or count")
			}
			result.Observations = append(result.Observations, observation(context, "network.port_summary", map[string]any{
				"address": address, "state": limited(ports.State), "count": ports.Count,
			}))
		}
		for _, script := range host.Scripts {
			if err := appendScript(address, "", 0, script); err != nil {
				return Result{}, err
			}
		}
		if len(result.Observations) > maxDecodedRecords {
			return Result{}, fmt.Errorf("Nmap report exceeds %d records", maxDecodedRecords)
		}
	}
	// Ports, service versions, and NSE output are evidence, not severity judgments.
	return result, nil
}

func decodeNikto(data []byte, context decodeContext) (Result, error) {
	var report struct {
		Scans []struct {
			Details []struct {
				Items []struct {
					ID          string `xml:"id,attr"`
					Method      string `xml:"method,attr"`
					Severity    string `xml:"severity,attr"`
					Description string `xml:"description"`
					URI         string `xml:"uri"`
					References  string `xml:"references"`
				} `xml:"item"`
			} `xml:"scandetails"`
		} `xml:"niktoscan"`
	}
	if err := decodeXML(data, "niktoscans", &report); err != nil {
		return Result{}, err
	}
	if len(report.Scans) == 0 {
		return Result{}, errors.New("Nikto report contains no scan")
	}
	var result Result
	for _, scan := range report.Scans {
		if len(scan.Details) == 0 {
			return Result{}, errors.New("Nikto report contains no scan details")
		}
		for _, details := range scan.Details {
			for _, item := range details.Items {
				if strings.TrimSpace(item.Description) == "" {
					return Result{}, errors.New("Nikto item is missing its description")
				}
				description := limited(item.Description)
				if item.URI != "" {
					if value, ok := resolveTargetURL(context.target.Value, strings.TrimSpace(item.URI)); ok {
						result.URLs = append(result.URLs, URLResult{URL: value, Visited: true})
						description += "\nURL: " + value
					}
				}
				description += "\n" + joinNonempty("Nikto test: "+limited(item.ID), limited(item.Method), limited(item.References))
				// Nikto normally supplies no severity. Never infer one from its test ID
				// or description; repeated IDs can identify different header checks.
				result.Findings = append(result.Findings, finding(context, "Nikto: "+item.Description, normalizeSeverity(item.Severity), description))
				if len(result.Findings) > maxDecodedRecords {
					return Result{}, fmt.Errorf("Nikto report exceeds %d records", maxDecodedRecords)
				}
			}
		}
	}
	return result, nil
}
