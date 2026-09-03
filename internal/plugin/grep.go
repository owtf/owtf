package plugin

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"regexp"

	"github.com/owtf/owtf/internal/model"
)

// TransactionParts declares which bodies a transaction reader should load.
type TransactionParts struct {
	RequestBody  bool
	ResponseBody bool
}

// CapturedTransaction is one immutable transaction plus only the bodies
// requested by a plugin.
type CapturedTransaction struct {
	Transaction  model.Transaction
	RequestBody  []byte
	ResponseBody []byte
}

// TransactionReader is the read-only evidence capability supplied to a grep
// plugin by the runner.
type TransactionReader interface {
	Range(context.Context, TransactionParts, func(CapturedTransaction) error) error
}

type compiledGrepRule struct {
	spec    GrepRule
	pattern *regexp.Regexp
}

// GrepExecutor evaluates bounded RE2 rules over retained target transactions.
// It records only transaction IDs, never copies matched content into output.
func GrepExecutor(manifest Manifest) Executor {
	spec := *manifest.Spec.Runtime.Grep
	rules := make([]compiledGrepRule, len(spec.Rules))
	parts := TransactionParts{}
	for index, rule := range spec.Rules {
		rules[index] = compiledGrepRule{spec: rule, pattern: regexp.MustCompile(rule.Pattern)}
		parts.RequestBody = parts.RequestBody || rule.Source == "request_body"
		parts.ResponseBody = parts.ResponseBody || rule.Source == "response_body"
	}
	techniqueCode := manifest.Spec.Techniques[0].Code
	targetKinds := append([]string(nil), manifest.Spec.TargetKinds...)

	return func(ctx context.Context, request Request) (Result, error) {
		if err := ctx.Err(); err != nil {
			return Result{}, err
		}
		if !supportsTarget(targetKinds, request.Target.Kind) {
			return Result{}, fmt.Errorf("plugin does not support %s targets", request.Target.Kind)
		}
		if request.Transactions == nil {
			return Result{}, errors.New("grep plugin requires captured transactions")
		}

		outputs := make([]model.GrepOutput, len(rules))
		for index, rule := range rules {
			outputs[index] = model.GrepOutput{
				RuleID: rule.spec.ID, Title: rule.spec.Title, Source: rule.spec.Source,
				TransactionIDs: []string{},
			}
		}
		transactionCount := 0
		matchCount := 0
		err := request.Transactions.Range(ctx, parts, func(transaction CapturedTransaction) error {
			transactionCount++
			for index, rule := range rules {
				if !rule.pattern.Match(grepSource(rule.spec.Source, transaction)) {
					continue
				}
				matchCount++
				if len(outputs[index].TransactionIDs) < spec.MaxMatches {
					outputs[index].TransactionIDs = append(outputs[index].TransactionIDs, transaction.Transaction.ID)
				} else {
					outputs[index].Truncated = true
				}
			}
			return nil
		})
		if err != nil {
			return Result{}, fmt.Errorf("read captured transactions: %w", err)
		}

		observations := make([]ObservationResult, len(outputs))
		for index, output := range outputs {
			data, err := json.Marshal(output)
			if err != nil {
				return Result{}, fmt.Errorf("encode grep output: %w", err)
			}
			observations[index] = ObservationResult{
				TechniqueCode: techniqueCode, Kind: model.ObservationKindGrepMatches, Data: string(data),
			}
		}
		request.Log("system", fmt.Sprintf("evaluated %d grep rules over %d transactions; %d matches", len(rules), transactionCount, matchCount))
		return Result{Observations: observations}, nil
	}
}

func grepSource(source string, transaction CapturedTransaction) []byte {
	switch source {
	case "url":
		return []byte(transaction.Transaction.URL)
	case "request_headers":
		return []byte(transaction.Transaction.RequestHeaders)
	case "response_headers":
		return []byte(transaction.Transaction.ResponseHeaders)
	case "request_body":
		return transaction.RequestBody
	case "response_body":
		return transaction.ResponseBody
	default:
		return nil
	}
}
