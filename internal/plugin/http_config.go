package plugin

import "net/http"

// ConfigureHTTP sets request defaults before the catalog is used by workers.
// Request contexts retain the runner's whole-task deadline. External commands
// and proxy forwarding are deliberately unaffected.
func (c *Catalog) ConfigureHTTP(client *http.Client, userAgent string) {
	c.RegisterBuiltin("http-collector", HTTPCollector(client, userAgent))
	for id, entry := range c.entries {
		if entry.Manifest.Spec.Runtime.Type == "http" {
			entry.Executor = HTTPExecutor(entry.Manifest, client, userAgent)
			c.entries[id] = entry
		}
	}
}
