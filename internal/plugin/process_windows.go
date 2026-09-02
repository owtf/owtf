//go:build windows

package plugin

import (
	"context"
	"os/exec"
)

func executeProcess(ctx context.Context, command *exec.Cmd) error {
	if err := command.Start(); err != nil {
		return err
	}
	done := make(chan error, 1)
	go func() { done <- command.Wait() }()
	select {
	case err := <-done:
		return err
	case <-ctx.Done():
		_ = command.Process.Kill()
		<-done
		return ctx.Err()
	}
}
