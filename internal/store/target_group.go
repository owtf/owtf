package store

import (
	"context"
	"net/url"
	"strings"

	"github.com/owtf/owtf/internal/model"
)

// targetHost groups exact hosts, never registrable domains or subdomains.
// URL execution identities, ports, paths and scope remain unchanged.
func targetHost(target model.Target) string {
	if target.Kind == "url" {
		if parsed, err := url.Parse(target.Value); err == nil {
			return strings.ToLower(parsed.Hostname())
		}
	}
	if target.Kind == "hostname" || target.Kind == "ip" {
		return strings.ToLower(target.Value)
	}
	return target.Kind + ":" + target.Value
}

// GetTargetGroupReport combines same-host evidence within one session without
// rewriting target IDs or broadening the scope of any execution.
func (s *Store) GetTargetGroupReport(ctx context.Context, id string, dispositions ...string) (model.TargetReport, error) {
	report, err := s.GetTargetReport(ctx, id, dispositions...)
	if err != nil {
		return report, err
	}
	targets, err := s.ListTargets(ctx, report.Target.SessionID)
	if err != nil {
		return model.TargetReport{}, err
	}
	report.Targets = []model.Target{report.Target}
	report.Host = targetHost(report.Target)
	for _, target := range targets {
		if target.ID == id || targetHost(target) != report.Host {
			continue
		}
		other, err := s.GetTargetReport(ctx, target.ID, dispositions...)
		if err != nil {
			return model.TargetReport{}, err
		}
		report.Targets = append(report.Targets, target)
		report.Tasks = append(report.Tasks, other.Tasks...)
		report.PluginOutputReviews = append(report.PluginOutputReviews, other.PluginOutputReviews...)
		report.PluginOutputReviewEvents = append(report.PluginOutputReviewEvents, other.PluginOutputReviewEvents...)
		report.URLs = append(report.URLs, other.URLs...)
		report.Attempts = append(report.Attempts, other.Attempts...)
		report.Events = append(report.Events, other.Events...)
		report.Artifacts = append(report.Artifacts, other.Artifacts...)
		report.Transactions = append(report.Transactions, other.Transactions...)
		report.Observations = append(report.Observations, other.Observations...)
		report.Findings = append(report.Findings, other.Findings...)
	}
	return report, nil
}
