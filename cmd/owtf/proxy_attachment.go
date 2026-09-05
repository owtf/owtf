package main

import (
	"context"
	"fmt"
	"net/url"
	"path/filepath"
	"time"

	"github.com/owtf/owtf/internal/artifact"
	"github.com/owtf/owtf/internal/har"
	"github.com/owtf/owtf/internal/model"
	"github.com/owtf/owtf/internal/proxy"
	"github.com/owtf/owtf/internal/store"
)

// openProxyAttachment uses the same durable evidence stores as the API. The
// feature is opt-in for standalone proxies and enabled by the Compose setup.
func openProxyAttachment(directory string) (*proxy.Attachment, func() error, error) {
	db, err := store.Open(filepath.Join(directory, "owtf.db"))
	if err != nil {
		return nil, nil, err
	}
	files, err := artifact.New(filepath.Join(directory, "artifacts"))
	if err != nil {
		db.Close()
		return nil, nil, err
	}
	validate := func(id string) error {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		target, err := db.GetTarget(ctx, id)
		if err != nil {
			return err
		}
		if target.Kind != "url" || !target.Scope {
			return fmt.Errorf("capture destination must be an in-scope URL target")
		}
		return nil
	}
	persist := func(id string, item har.Transaction) error {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		target, err := db.GetTarget(ctx, id)
		if err != nil {
			return err
		}
		if !target.Scope {
			return fmt.Errorf("capture target is now out of scope")
		}
		origin, err := url.Parse(target.Value)
		if err != nil {
			return err
		}
		destination, err := url.Parse(item.URL)
		if err != nil {
			return err
		}
		// Explicit origin matching avoids silently claiming traffic to other ports,
		// protocols or subdomains. Paths under this origin remain distinct URLs.
		if origin.Scheme != destination.Scheme || origin.Host != destination.Host {
			return nil
		}
		transaction := model.Transaction{ID: store.NewID("txn"), TargetID: id, Method: item.Method, URL: item.URL, RequestHeaders: item.RequestHeaders, StatusCode: item.StatusCode, ResponseHeaders: item.ResponseHeaders, DurationMS: item.DurationMS, CreatedAt: item.StartedAt}
		artifacts := []model.Artifact{}
		for _, body := range []struct {
			name, media string
			data        []byte
			id          *string
		}{
			{"request-body", item.RequestMediaType, item.RequestBody, &transaction.RequestBodyArtifactID},
			{"response-body", item.ResponseMediaType, item.ResponseBody, &transaction.ResponseBodyArtifactID},
		} {
			if len(body.data) == 0 {
				continue
			}
			stored, err := files.Put(body.data)
			if err != nil {
				return err
			}
			*body.id = store.NewID("art")
			media := body.media
			if media == "" {
				media = "application/octet-stream"
			}
			artifacts = append(artifacts, model.Artifact{ID: *body.id, TargetID: id, Name: body.name, MediaType: media, Size: stored.Size, SHA256: stored.SHA256, Path: stored.Path, CreatedAt: item.StartedAt})
		}
		return db.ImportTransactions(ctx, id, artifacts, []model.Transaction{transaction})
	}
	return proxy.NewAttachment(validate, persist), db.Close, nil
}
