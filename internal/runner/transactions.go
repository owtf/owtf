package runner

import (
	"context"
	"fmt"
	"io"

	"github.com/owtf/owtf/internal/artifact"
	"github.com/owtf/owtf/internal/plugin"
	"github.com/owtf/owtf/internal/store"
)

const (
	maxGrepTransactionCount = 10_000
	maxGrepBodyBytes        = 8 << 20
)

type transactionReader struct {
	store     *store.Store
	artifacts *artifact.Store
	targetID  string
}

func (reader transactionReader) Range(ctx context.Context, parts plugin.TransactionParts, visit func(plugin.CapturedTransaction) error) error {
	transactions, err := reader.store.ListTargetTransactionsBounded(ctx, reader.targetID, maxGrepTransactionCount+1)
	if err != nil {
		return err
	}
	if len(transactions) > maxGrepTransactionCount {
		return fmt.Errorf("target has more than %d transactions", maxGrepTransactionCount)
	}
	for _, transaction := range transactions {
		if err := ctx.Err(); err != nil {
			return err
		}
		captured := plugin.CapturedTransaction{Transaction: transaction}
		bodies := make(map[string][]byte, 2)
		readBody := func(artifactID string) ([]byte, error) {
			if artifactID == "" {
				return nil, nil
			}
			if body, ok := bodies[artifactID]; ok {
				return body, nil
			}
			body, err := reader.readBody(ctx, artifactID)
			if err == nil {
				bodies[artifactID] = body
			}
			return body, err
		}
		if parts.RequestBody {
			captured.RequestBody, err = readBody(transaction.RequestBodyArtifactID)
			if err != nil {
				return fmt.Errorf("read transaction %s request body: %w", transaction.ID, err)
			}
		}
		if parts.ResponseBody {
			captured.ResponseBody, err = readBody(transaction.ResponseBodyArtifactID)
			if err != nil {
				return fmt.Errorf("read transaction %s response body: %w", transaction.ID, err)
			}
		}
		if err := visit(captured); err != nil {
			return err
		}
	}
	return nil
}

func (reader transactionReader) readBody(ctx context.Context, artifactID string) ([]byte, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	metadata, err := reader.store.GetArtifact(ctx, artifactID)
	if err != nil {
		return nil, err
	}
	if metadata.TargetID != reader.targetID {
		return nil, fmt.Errorf("artifact belongs to target %s", metadata.TargetID)
	}
	if metadata.Size > maxGrepBodyBytes {
		return nil, fmt.Errorf("artifact exceeds %d bytes", maxGrepBodyBytes)
	}
	file, err := reader.artifacts.Open(metadata.Path)
	if err != nil {
		return nil, err
	}
	body, readErr := io.ReadAll(io.LimitReader(file, maxGrepBodyBytes+1))
	closeErr := file.Close()
	if readErr != nil {
		return nil, readErr
	}
	if closeErr != nil {
		return nil, closeErr
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if len(body) > maxGrepBodyBytes {
		return nil, fmt.Errorf("artifact exceeds %d bytes", maxGrepBodyBytes)
	}
	if int64(len(body)) != metadata.Size {
		return nil, fmt.Errorf("artifact size is %d bytes, expected %d", len(body), metadata.Size)
	}
	return body, nil
}
