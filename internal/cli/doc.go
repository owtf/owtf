// Package cli implements the scriptable OWTF command-line client.
//
// Commands use the public HTTP API rather than opening SQLite or invoking the
// runner directly. This keeps browser, CLI, and automation behavior on one
// control-plane path.
package cli
