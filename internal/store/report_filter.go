package store

import (
	"fmt"
	"strings"

	"github.com/owtf/owtf/internal/model"
)

// filterTargetReport selects task outputs by their current disposition. History
// follows the selected task, including earlier dispositions. Independent target
// evidence stays available because it has no output review to filter against.
func filterTargetReport(report *model.TargetReport, values []string) error {
	selected := make(map[string]bool)
	dispositions := make([]string, 0)
	for _, value := range values {
		for _, disposition := range strings.Split(value, ",") {
			disposition = strings.TrimSpace(disposition)
			if !validPluginOutputDisposition(disposition) {
				return fmt.Errorf("%w: unsupported report disposition %q", ErrInvalid, disposition)
			}
			if !selected[disposition] {
				dispositions = append(dispositions, disposition)
				selected[disposition] = true
			}
		}
	}
	if len(selected) == 0 {
		return nil
	}
	report.Dispositions = dispositions
	reviews := make(map[string]string)
	for _, review := range report.PluginOutputReviews {
		reviews[review.TaskID] = review.Disposition
	}
	tasks := make(map[string]bool)
	for _, task := range report.Tasks {
		disposition := reviews[task.ID]
		if disposition == "" {
			disposition = model.PluginOutputDispositionOpen
		}
		tasks[task.ID] = selected[disposition]
	}
	report.Tasks = selectReportRows(report.Tasks, func(v model.Task) bool { return tasks[v.ID] })
	report.PluginOutputReviews = selectReportRows(report.PluginOutputReviews, func(v model.PluginOutputReview) bool { return tasks[v.TaskID] })
	report.PluginOutputReviewEvents = selectReportRows(report.PluginOutputReviewEvents, func(v model.PluginOutputReviewEvent) bool { return tasks[v.TaskID] })
	report.Attempts = selectReportRows(report.Attempts, func(v model.TaskAttempt) bool { return tasks[v.TaskID] })
	report.Events = selectReportRows(report.Events, func(v model.TaskEvent) bool { return tasks[v.TaskID] })
	report.Observations = selectReportRows(report.Observations, func(v model.Observation) bool { return tasks[v.TaskID] })
	report.Findings = selectReportRows(report.Findings, func(v model.Finding) bool { return tasks[v.TaskID] })
	report.Transactions = selectReportRows(report.Transactions, func(v model.Transaction) bool { return v.TaskID == "" || tasks[v.TaskID] })
	// Retain artifacts referenced by included transactions even when their producer
	// has a different disposition, so exported evidence links remain usable.
	referenced := make(map[string]bool)
	for _, tx := range report.Transactions {
		referenced[tx.SourceArtifactID] = true
		referenced[tx.RequestBodyArtifactID] = true
		referenced[tx.ResponseBodyArtifactID] = true
	}
	report.Artifacts = selectReportRows(report.Artifacts, func(v model.Artifact) bool { return v.TaskID == "" || tasks[v.TaskID] || referenced[v.ID] })
	return nil
}

func filterSessionReport(report *model.SessionReport, values []string) error {
	outputs := model.TargetReport{
		Tasks: report.Tasks, PluginOutputReviews: report.PluginOutputReviews,
		PluginOutputReviewEvents: report.PluginOutputReviewEvents,
		Attempts:                 report.Attempts, Events: report.Events, Observations: report.Observations,
		Findings: report.Findings, Transactions: report.Transactions, Artifacts: report.Artifacts,
	}
	if err := filterTargetReport(&outputs, values); err != nil {
		return err
	}
	report.Dispositions = outputs.Dispositions
	report.Tasks, report.PluginOutputReviews = outputs.Tasks, outputs.PluginOutputReviews
	report.PluginOutputReviewEvents = outputs.PluginOutputReviewEvents
	report.Attempts, report.Events = outputs.Attempts, outputs.Events
	report.Observations, report.Findings = outputs.Observations, outputs.Findings
	report.Transactions, report.Artifacts = outputs.Transactions, outputs.Artifacts
	report.Summary = summarizeReport(*report)
	return nil
}

// selectReportRows allocates a view without modifying the source slice.
func selectReportRows[T any](rows []T, keep func(T) bool) []T {
	result := make([]T, 0, len(rows))
	for _, row := range rows {
		if keep(row) {
			result = append(result, row)
		}
	}
	return result
}
