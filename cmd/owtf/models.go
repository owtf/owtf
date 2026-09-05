package main

import (
	"context"
	"errors"
	"flag"
	"io"
	"os"
	"os/signal"
	"sort"
	"syscall"

	"github.com/owtf/owtf/internal/ai"
)

// runModels keeps qualification operator-invoked and outside the unauthenticated
// API. Listing configuration is offline; only check can contact a provider.
func runModels(args []string, stdout, stderr io.Writer) error {
	if len(args) == 0 || (args[0] != "list" && args[0] != "check") {
		return errors.New("usage: owtf models list|check [--config FILE] [--model ALIAS]")
	}
	flags := flag.NewFlagSet("owtf models "+args[0], flag.ContinueOnError)
	flags.SetOutput(stderr)
	path := flags.String("config", defaultConfigurationPath(), "configuration file")
	var alias string
	if args[0] == "check" {
		flags.StringVar(&alias, "model", "", "model alias (defaults to ai.defaultModel)")
	}
	if err := flags.Parse(args[1:]); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("models accepts no positional arguments after list or check")
	}
	settings, err := effectiveConfiguration(*path)
	if err != nil {
		return err
	}
	if args[0] == "list" {
		type entry struct {
			Alias    string `json:"alias"`
			Provider string `json:"provider"`
			Protocol string `json:"protocol"`
			Model    string `json:"model"`
			Default  bool   `json:"default"`
		}
		entries := make([]entry, 0, len(settings.AI.Models))
		for name, model := range settings.AI.Models {
			entries = append(entries, entry{name, model.Provider, settings.AI.Providers[model.Provider].Protocol, model.Model, name == settings.AI.DefaultModel})
		}
		sort.Slice(entries, func(i, j int) bool { return entries[i].Alias < entries[j].Alias })
		return writeConfigurationJSON(stdout, entries)
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	result, err := ai.Check(ctx, settings.AI, alias)
	if err != nil {
		return err
	}
	return writeConfigurationJSON(stdout, result)
}
