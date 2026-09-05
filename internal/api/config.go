package api

import (
	"net/http"

	owtfconfig "github.com/owtf/owtf/internal/config"
)

func (s *Server) getConfig(w http.ResponseWriter, r *http.Request) {
	if s.runtimeConfig == nil {
		writeError(w, http.StatusServiceUnavailable, "startup configuration unavailable")
		return
	}
	writeJSON(w, http.StatusOK, s.runtimeConfig)
}

func (s *Server) validateConfig(w http.ResponseWriter, r *http.Request) {
	var input struct {
		YAML string `json:"yaml"`
	}
	if err := decodeJSON(w, r, &input); err != nil {
		return
	}
	if _, err := owtfconfig.Parse([]byte(input.YAML)); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]bool{"valid": true})
}
