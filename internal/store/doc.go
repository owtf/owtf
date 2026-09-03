// Package store persists OWTF sessions, targets, plugin runs, worklist entries,
// transactions, artifacts, and reports in SQLite.
//
// The store owns transactional state changes but does not execute plugins or
// write artifact bytes. Public IDs are stable API identifiers; integer primary
// keys remain an internal SQLite detail.
package store
