package main

import (
	"bytes"
	"log/slog"
	"strings"
	"testing"
)

func TestProcessLogLevels(t *testing.T) {
	for i, level := range []string{"debug", "info", "warn", "error"} {
		t.Run(level, func(t *testing.T) {
			var output bytes.Buffer
			restore := configureLogging(&output, level)
			defer restore()
			slog.Debug("debug-message")
			slog.Info("info-message")
			slog.Warn("warn-message")
			slog.Error("error-message")
			slog.NewLogLogger(slog.Default().Handler(), slog.LevelError).Print("http-error")
			for j, message := range []string{"debug-message", "info-message", "warn-message", "error-message"} {
				if strings.Contains(output.String(), message) != (j >= i) {
					t.Fatalf("level=%s output=%s", level, &output)
				}
			}
			if !strings.Contains(output.String(), "http-error") {
				t.Fatal("HTTP errors suppressed")
			}
		})
	}
}

func TestDiagnosticAndHTTPFlags(t *testing.T) {
	t.Setenv("OWTF_LOG_LEVEL", "warn")
	t.Setenv("OWTF_HTTP_USER_AGENT", "environment")
	settings, err := serverConfiguration([]string{"--log-level", "debug", "--http-user-agent", "flag-agent", "--http-request-timeout", "7"}, &bytes.Buffer{})
	if err != nil {
		t.Fatal(err)
	}
	if settings.LogLevel != "debug" || settings.HTTP.UserAgent != "flag-agent" || settings.HTTP.RequestTimeoutSeconds != 7 {
		t.Fatalf("%+v", settings)
	}
	settings, err = proxyConfiguration([]string{"--log-level", "error"}, &bytes.Buffer{})
	if err != nil || settings.LogLevel != "error" {
		t.Fatalf("%+v %v", settings, err)
	}
}
