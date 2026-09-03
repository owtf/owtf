package plugin

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/owtf/owtf/internal/model"
)

// ExternalExecutor records curated testing guidance without contacting the
// target or starting another process.
func ExternalExecutor(manifest Manifest) Executor {
	external := *manifest.Spec.Runtime.External
	external.References = append([]model.ExternalReference(nil), external.References...)
	techniqueCode := manifest.Spec.Techniques[0].Code
	targetKinds := append([]string(nil), manifest.Spec.TargetKinds...)

	return func(ctx context.Context, request Request) (Result, error) {
		if err := ctx.Err(); err != nil {
			return Result{}, err
		}
		if !supportsTarget(targetKinds, request.Target.Kind) {
			return Result{}, fmt.Errorf("plugin does not support %s targets", request.Target.Kind)
		}
		data, err := json.Marshal(model.ExternalOutput{
			Guidance: external.Guidance, References: external.References,
		})
		if err != nil {
			return Result{}, fmt.Errorf("encode external guidance: %w", err)
		}
		request.Log("system", fmt.Sprintf("recorded %d external references", len(external.References)))
		return Result{Observations: []ObservationResult{{
			TechniqueCode: techniqueCode,
			Kind:          model.ObservationKindExternalReferences,
			Data:          string(data),
		}}}, nil
	}
}
