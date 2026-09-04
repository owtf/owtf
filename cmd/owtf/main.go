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
	"syscall"
	"time"

	"github.com/owtf/owtf/internal/api"
	"github.com/owtf/owtf/internal/artifact"
	"github.com/owtf/owtf/internal/cli"
	owtfconfig "github.com/owtf/owtf/internal/config"
	helpinfo "github.com/owtf/owtf/internal/help"
	"github.com/owtf/owtf/internal/model"
	"github.com/owtf/owtf/internal/plugin"
	"github.com/owtf/owtf/internal/profile"
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
			return runServe(args[1:], stdout, stderr)
		case "proxy":
			return runProxyCommand(context.Background(), args[1:], stdout, stderr)
		case "config":
			return runConfig(args[1:], stdout, stderr)
		default:
			return cli.Run(context.Background(), args, stdout, stderr)
		}
	}
	return runServe(nil, stdout, stderr)
}

func serve(settings owtfconfig.Config) error {
	dataDir := settings.Server.DataDirectory
	database, err := store.Open(filepath.Join(dataDir, "owtf.db"))
	if err != nil {
		return err
	}
	defer database.Close()

	artifacts, err := artifact.New(filepath.Join(dataDir, "artifacts"))
	if err != nil {
		return err
	}
	catalog, err := plugin.Load(os.DirFS(settings.Plugins.Directory))
	if err != nil {
		return fmt.Errorf("load plugins: %w", err)
	}
	catalog.ConfigureHTTP(&http.Client{Timeout: time.Duration(settings.HTTP.RequestTimeoutSeconds) * time.Second}, settings.HTTP.UserAgent)
	catalog.ResolveCommands(settings.Plugins.WordlistDirectory)
	catalog.ResolveContainers(context.Background(), plugin.NewDockerEngine(settings.Plugins.ContainerEngine), settings.Plugins.WordlistDirectory)
	profiles, err := profile.Load(os.DirFS(settings.Plugins.ProfilesDirectory))
	if err != nil {
		return fmt.Errorf("load profiles: %w", err)
	}
	if err := profiles.ValidatePlugins(catalog); err != nil {
		return fmt.Errorf("validate profiles: %w", err)
	}
	if _, ok := profiles.Get(settings.Plugins.DefaultProfile); !ok {
		return fmt.Errorf("default profile %q does not exist", settings.Plugins.DefaultProfile)
	}
	plugins := make([]model.Plugin, 0, len(catalog.Entries()))
	for _, entry := range catalog.Entries() {
		plugins = append(plugins, entry.Plugin())
	}
	if err := database.ReplacePlugins(context.Background(), plugins); err != nil {
		return fmt.Errorf("index plugins: %w", err)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	workerCount := settings.Server.Workers
	taskTimeout := time.Duration(settings.Server.TaskTimeoutSeconds) * time.Second
	taskRunner := runner.New(database, artifacts, catalog, workerCount, taskTimeout)
	if err := taskRunner.Start(ctx); err != nil {
		return err
	}
	defer taskRunner.Stop()

	server := &http.Server{
		Addr:     settings.Server.Address,
		ErrorLog: slog.NewLogLogger(slog.Default().Handler(), slog.LevelError),
		Handler: api.New(api.Config{
			Store: database, Artifacts: artifacts, Plugins: catalog,
			Profiles: profiles, Help: helpinfo.Default(), DefaultProfile: settings.Plugins.DefaultProfile, Runner: taskRunner,
		}),
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
