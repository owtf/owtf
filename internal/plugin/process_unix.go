//go:build !windows

package plugin

import (
	"context"
	"errors"
	"os/exec"
	"syscall"
	"time"
)

func executeProcess(ctx context.Context, command *exec.Cmd) error {
	command.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
	// Orphaned children can keep output pipes open after the parent exits.
	command.WaitDelay = time.Second
	if err := command.Start(); err != nil {
		return err
	}
	done := make(chan error, 1)
	go func() { done <- command.Wait() }()
	select {
	case err := <-done:
		_ = signalProcessGroup(command.Process.Pid, syscall.SIGKILL)
		return err
	case <-ctx.Done():
		_ = signalProcessGroup(command.Process.Pid, syscall.SIGTERM)
	}

	timer := time.NewTimer(750 * time.Millisecond)
	exited := false
	select {
	case <-done:
		exited = true
	case <-timer.C:
	}
	if !timer.Stop() && !exited {
		select {
		case <-timer.C:
		default:
		}
	}
	_ = signalProcessGroup(command.Process.Pid, syscall.SIGKILL)
	if !exited {
		<-done
	}
	return ctx.Err()
}

func signalProcessGroup(pid int, signal syscall.Signal) error {
	err := syscall.Kill(-pid, signal)
	if errors.Is(err, syscall.ESRCH) {
		return nil
	}
	return err
}
