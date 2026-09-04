package main

import (
	"io"
	"log/slog"
)

// configureLogging scopes process diagnostics to one server command. Task
// evidence uses the runner's persistent event path and is not filtered here.
func configureLogging(output io.Writer, name string) func() {
	level := slog.LevelInfo
	switch name {
	case "debug":
		level = slog.LevelDebug
	case "warn":
		level = slog.LevelWarn
	case "error":
		level = slog.LevelError
	}
	previous := slog.Default()
	slog.SetDefault(slog.New(slog.NewTextHandler(output, &slog.HandlerOptions{Level: level})))
	return func() { slog.SetDefault(previous) }
}
