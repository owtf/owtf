PROJ := owtf
SHELL := /bin/bash

DOCKER_COMPOSE_CMD := $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; elif docker-compose --version >/dev/null 2>&1; then echo "docker-compose"; fi)
COMPOSE := $(DOCKER_COMPOSE_CMD) -p $(PROJ) -f docker/docker-compose.yml

OWTF_GO_PATH ?= /tmp/owtf-go
OWTF_GO_CACHE ?= /tmp/owtf-go-cache
OWTF_GO_ENV := GOPATH=$(OWTF_GO_PATH) GOMODCACHE=$(OWTF_GO_PATH)/pkg/mod GOCACHE=$(OWTF_GO_CACHE) GOMAXPROCS=2

.PHONY: build check-compose clean fmt fmt-check lint local-down local-logs local-status local-up run test test-unit test-api test-tools test-failures tools-image vet

build:
	@echo "--> Building OWTF"
	@mkdir -p build
	@env $(OWTF_GO_ENV) go build -trimpath -o build/owtf ./cmd/owtf

run:
	@env $(OWTF_GO_ENV) go run ./cmd/owtf serve

fmt:
	@gofmt -w $$(find cmd internal -name '*.go' -type f)

fmt-check:
	@files="$$(gofmt -l $$(find cmd internal -name '*.go' -type f))"; \
		test -z "$$files" || { echo "These files need gofmt:"; echo "$$files"; exit 1; }

vet:
	@env $(OWTF_GO_ENV) go vet ./...

lint: fmt-check vet

test-unit:
	@echo "--> Testing OWTF"
	@env $(OWTF_GO_ENV) go test -p=1 ./...

test-api:
	@echo "--> Exercising the API and CLI through a real local server"
	@OWTF_SMOKE_GOPATH=$(OWTF_GO_PATH) OWTF_SMOKE_GOMODCACHE=$(OWTF_GO_PATH)/pkg/mod ./scripts/owtf-smoke.sh

tools-image:
	@echo "--> Building the Kali plugin tools image"
	@docker build --file docker/Dockerfile.tools --tag owtf/kali-tools:local .

test-tools: check-compose
	@echo "--> Exercising retained scanner tools against isolated fixtures"
	@docker image inspect owtf/kali-tools:local >/dev/null 2>&1 || { \
		echo "Missing owtf/kali-tools:local. Run: make tools-image"; exit 1; \
	}
	@./scripts/owtf-tools-smoke.sh

test-failures:
	@echo "--> Checking active-scan cancellation, crashes, and timeouts"
	@./scripts/owtf-tools-smoke.sh --failure-only

test: lint test-unit test-api

check-compose:
ifeq ($(strip $(DOCKER_COMPOSE_CMD)),)
	$(error Docker Compose not found. Install the Docker Compose plugin)
endif

local-up: check-compose
	@echo "--> Starting OWTF on http://localhost:8009"
	@$(COMPOSE) up -d --build

local-down: check-compose
	@$(COMPOSE) down

local-status: check-compose
	@$(COMPOSE) ps

local-logs: check-compose
	@$(COMPOSE) logs -f owtf

clean:
	@rm -rf build
	@env GOCACHE=$(OWTF_GO_CACHE) go clean -cache
