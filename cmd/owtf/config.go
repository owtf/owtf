package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"github.com/owtf/owtf/internal/cli"
	owtfconfig "github.com/owtf/owtf/internal/config"
)

func runServe(args []string, stdout, stderr io.Writer) error {
	settings, err := serverConfiguration(args, stderr)
	if err != nil {
		return err
	}
	cli.WriteBanner(stdout)
	return serve(settings)
}

func serverConfiguration(args []string, stderr io.Writer) (owtfconfig.Config, error) {
	path, err := configurationPath(args)
	if err != nil {
		return owtfconfig.Config{}, err
	}
	settings, err := effectiveConfiguration(path)
	if err != nil {
		return owtfconfig.Config{}, err
	}

	flags := flag.NewFlagSet("owtf serve", flag.ContinueOnError)
	flags.SetOutput(stderr)
	flags.String("config", path, "configuration file")
	flags.StringVar(&settings.Server.Address, "addr", settings.Server.Address, "server listen address")
	flags.StringVar(&settings.Server.DataDirectory, "data-dir", settings.Server.DataDirectory, "data directory")
	flags.IntVar(&settings.Server.Workers, "workers", settings.Server.Workers, "worker count")
	flags.StringVar(&settings.Plugins.Directory, "plugin-dir", settings.Plugins.Directory, "plugin directory")
	flags.StringVar(&settings.Plugins.ProfilesDirectory, "profile-dir", settings.Plugins.ProfilesDirectory, "plugin profile directory")
	flags.StringVar(&settings.Plugins.DefaultProfile, "profile", settings.Plugins.DefaultProfile, "default plugin profile")
	flags.StringVar(&settings.Plugins.ContainerEngine, "container-engine", settings.Plugins.ContainerEngine, "container engine executable")
	taskTimeout := time.Duration(settings.Server.TaskTimeoutSeconds) * time.Second
	flags.DurationVar(&taskTimeout, "task-timeout", taskTimeout, "maximum plugin task duration")
	if err := flags.Parse(args); err != nil {
		return owtfconfig.Config{}, err
	}
	if flags.NArg() != 0 {
		return owtfconfig.Config{}, errors.New("serve accepts no positional arguments")
	}
	if taskTimeout < time.Second || taskTimeout%time.Second != 0 {
		return owtfconfig.Config{}, errors.New("task timeout must be a whole number of seconds")
	}
	settings.Server.TaskTimeoutSeconds = int(taskTimeout / time.Second)
	if err := settings.Validate(); err != nil {
		return owtfconfig.Config{}, err
	}
	return settings, nil
}

func runConfig(args []string, stdout, stderr io.Writer) error {
	if len(args) == 0 {
		return errors.New("config requires show or validate")
	}
	switch args[0] {
	case "show":
		flags := flag.NewFlagSet("owtf config show", flag.ContinueOnError)
		flags.SetOutput(stderr)
		path := flags.String("config", defaultConfigurationPath(), "configuration file")
		if err := flags.Parse(args[1:]); err != nil {
			return err
		}
		if flags.NArg() != 0 {
			return errors.New("config show accepts no positional arguments")
		}
		settings, err := effectiveConfiguration(*path)
		if err != nil {
			return err
		}
		return writeConfigurationJSON(stdout, settings.Redacted())
	case "validate":
		if len(args) != 2 || strings.TrimSpace(args[1]) == "" {
			return errors.New("usage: owtf config validate FILE")
		}
		if _, err := owtfconfig.Load(args[1]); err != nil {
			return err
		}
		return writeConfigurationJSON(stdout, map[string]any{"path": args[1], "valid": true})
	default:
		return fmt.Errorf("unknown config command %q", args[0])
	}
}

func effectiveConfiguration(path string) (owtfconfig.Config, error) {
	settings, err := owtfconfig.LoadOptional(path)
	if err != nil {
		return owtfconfig.Config{}, err
	}
	if err := settings.ApplyEnvironment(os.LookupEnv); err != nil {
		return owtfconfig.Config{}, err
	}
	return settings, nil
}

func configurationPath(args []string) (string, error) {
	path := defaultConfigurationPath()
	for index := 0; index < len(args); index++ {
		switch argument := args[index]; {
		case argument == "--config":
			index++
			if index == len(args) || strings.TrimSpace(args[index]) == "" {
				return "", errors.New("--config requires a file path")
			}
			path = args[index]
		case strings.HasPrefix(argument, "--config="):
			path = strings.TrimPrefix(argument, "--config=")
			if strings.TrimSpace(path) == "" {
				return "", errors.New("--config requires a file path")
			}
		}
	}
	return path, nil
}

func defaultConfigurationPath() string {
	return env("OWTF_CONFIG", owtfconfig.DefaultPath)
}

func writeConfigurationJSON(output io.Writer, value any) error {
	encoder := json.NewEncoder(output)
	encoder.SetIndent("", "  ")
	return encoder.Encode(value)
}
