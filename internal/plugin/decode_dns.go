package plugin

import (
	"fmt"
	"net/netip"
	"sort"
	"strings"

	"github.com/owtf/owtf/internal/target"
)

// decodeGobusterDNS accepts Gobuster 3.8's uncolored hostname/address records.
// DNS answers are observations, not URLs, new scan targets, or vulnerabilities.
// Wildcard detection is left enabled in the manifest and aborts the tool before
// dictionary enumeration; that failure and its diagnostic remain in task logs.
func decodeGobusterDNS(data []byte, context decodeContext) (Result, error) {
	base, err := target.Normalize(context.target.Value)
	if err != nil || base.Kind != "hostname" || context.target.Kind != "hostname" {
		return Result{}, fmt.Errorf("DNS discovery requires a hostname target")
	}
	lines, err := scanLines(data)
	if err != nil {
		return Result{}, err
	}
	answers := make(map[string]map[string]bool)
	for index, line := range lines {
		fields := strings.Fields(line)
		if len(fields) != 2 {
			return Result{}, fmt.Errorf("DNS record %d must contain a hostname and IP addresses", index+1)
		}
		name, err := target.Normalize(fields[0])
		if err != nil || name.Kind != "hostname" || !strings.HasSuffix(name.Value, "."+base.Value) {
			return Result{}, fmt.Errorf("DNS record %d is not below the target hostname", index+1)
		}
		if answers[name.Value] == nil {
			answers[name.Value] = make(map[string]bool)
		}
		for _, value := range strings.Split(fields[1], ",") {
			address, err := netip.ParseAddr(value)
			if err != nil || address.Zone() != "" {
				return Result{}, fmt.Errorf("DNS record %d contains an invalid IP address", index+1)
			}
			answers[name.Value][address.Unmap().String()] = true
		}
	}
	names := make([]string, 0, len(answers))
	for name := range answers {
		names = append(names, name)
	}
	sort.Strings(names)
	var result Result
	for _, name := range names {
		addresses := make([]string, 0, len(answers[name]))
		for address := range answers[name] {
			addresses = append(addresses, address)
		}
		sort.Strings(addresses)
		result.Observations = append(result.Observations, observation(context, "dns.name", map[string]any{
			"hostname": name, "addresses": addresses,
		}))
	}
	return result, nil
}
