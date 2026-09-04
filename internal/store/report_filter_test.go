package store

import (
	"github.com/owtf/owtf/internal/model"
	"testing"
)

func TestReportDispositionSelection(t *testing.T) {
	original := model.SessionReport{
		Tasks:                    []model.Task{{ID: "a", Status: model.TaskSucceeded}, {ID: "b", Status: model.TaskFailed}},
		PluginOutputReviews:      []model.PluginOutputReview{{TaskID: "a", Disposition: "confirmed"}},
		PluginOutputReviewEvents: []model.PluginOutputReviewEvent{{TaskID: "a", Disposition: "open"}, {TaskID: "a", Disposition: "confirmed"}},
		Artifacts:                []model.Artifact{{ID: "a", TaskID: "a"}, {ID: "b", TaskID: "b"}, {ID: "shared"}},
		Transactions:             []model.Transaction{{ID: "independent", SourceArtifactID: "b"}, {ID: "excluded", TaskID: "b"}},
	}
	filtered := original
	if err := filterSessionReport(&filtered, []string{"confirmed,confirmed"}); err != nil {
		t.Fatal(err)
	}
	if len(filtered.Tasks) != 1 || len(filtered.PluginOutputReviewEvents) != 2 || len(filtered.Artifacts) != 3 || len(filtered.Transactions) != 1 || filtered.Summary.Tasks != 1 || filtered.Summary.Succeeded != 1 || len(filtered.Dispositions) != 1 {
		t.Fatalf("unexpected report: %+v", filtered)
	}
	if len(original.Tasks) != 2 || original.Tasks[1].ID != "b" {
		t.Fatal("filter changed source")
	}
	filtered = original
	if err := filterSessionReport(&filtered, []string{"open"}); err != nil {
		t.Fatal(err)
	}
	if len(filtered.Tasks) != 1 || filtered.Tasks[0].ID != "b" || len(filtered.PluginOutputReviewEvents) != 0 {
		t.Fatalf("default open: %+v", filtered)
	}
	for _, value := range []string{"", "confirmed,", "unknown"} {
		if err := filterSessionReport(&filtered, []string{value}); err == nil {
			t.Fatalf("accepted %q", value)
		}
	}
}
