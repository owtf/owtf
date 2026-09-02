// Package store persists OWTF control-plane state in SQLite.
//
// The store owns transactional state changes but does not execute plugins or
// write artifact bytes. Public IDs are stable API identifiers; integer primary
// keys remain an internal SQLite detail.
package store
