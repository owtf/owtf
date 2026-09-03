package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"syscall"
	"time"

	"github.com/owtf/owtf/internal/api"
	"github.com/owtf/owtf/internal/artifact"
	"github.com/owtf/owtf/internal/cli"
	"github.com/owtf/owtf/internal/model"
	"github.com/owtf/owtf/internal/plugin"
	"github.com/owtf/owtf/internal/runner"
	"github.com/owtf/owtf/internal/store"
)

func main() {
	if err := run(os.Args[1:], os.Stdout, os.Stderr); err != nil {
		fmt.Fprintln(os.Stderr, "owtf:", err)
		os.Exit(1)
	}
}

func run(args []string, stdout, stderr io.Writer) error {
	if len(args) > 0 {
		switch args[0] {
		case "serve":
			if len(args) > 1 {
				return fmt.Errorf("serve accepts no arguments")
			}
		case "proxy":
			return runProxyCommand(context.Background(), args[1:], stdout, stderr)
		default:
			return cli.Run(context.Background(), args, stdout, stderr)
		}
	}
	return serve()
}

func serve() error {
	dataDir := env("OWTF_DATA_DIR", ".owtf")
	database, err := store.Open(filepath.Join(dataDir, "owtf.db"))
	if err != nil {
		return err
	}
	defer database.Close()

	artifacts, err := artifact.New(filepath.Join(dataDir, "artifacts"))
	if err != nil {
		return err
	}
	catalog, err := plugin.Load(os.DirFS(env("OWTF_PLUGIN_DIR", "plugins")))
	if err != nil {
		return fmt.Errorf("load plugins: %w", err)
	}
	catalog.RegisterBuiltin("http-collector", plugin.HTTPCollector(nil))
	catalog.ResolveCommands()
	catalog.ResolveContainers(context.Background(), plugin.NewDockerEngine(env("OWTF_CONTAINER_ENGINE", "docker")))
	plugins := make([]model.Plugin, 0, len(catalog.Entries()))
	for _, entry := range catalog.Entries() {
		plugins = append(plugins, entry.Plugin())
	}
	if err := database.ReplacePlugins(context.Background(), plugins); err != nil {
		return fmt.Errorf("index plugins: %w", err)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	workerCount := envInt("OWTF_WORKERS", 1)
	taskRunner := runner.New(database, artifacts, catalog, workerCount, 30*time.Second)
	if err := taskRunner.Start(ctx); err != nil {
		return err
	}
	defer taskRunner.Stop()

	server := &http.Server{
		Addr:              env("OWTF_ADDR", ":8009"),
		Handler:           api.New(database, artifacts, catalog, taskRunner),
		ReadHeaderTimeout: 5 * time.Second,
		IdleTimeout:       60 * time.Second,
	}
	go func() {
		<-ctx.Done()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = server.Shutdown(shutdownCtx)
	}()
	slog.Info("OWTF listening", "address", server.Addr, "workers", workerCount, "data", dataDir)
	if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		return err
	}
	return nil
}

func env(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func envInt(key string, fallback int) int {
	value, err := strconv.Atoi(os.Getenv(key))
	if err != nil || value < 1 {
		return fallback
	}
	return value
}
