.PHONY: help build up down logs ps test security-scan certs

COMPOSE_PROD = docker compose -f infra/docker-compose.prod.yml
API_IMAGE    = neuroflow-api:latest

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Docker lifecycle
# ---------------------------------------------------------------------------
certs: ## Generate self-signed TLS certs for local Nginx
	@bash infra/gen_certs.sh

build: ## Build all production images
	$(COMPOSE_PROD) build

up: ## Start all production services (detached)
	$(COMPOSE_PROD) up -d

down: ## Stop and remove all production containers
	$(COMPOSE_PROD) down

logs: ## Tail logs from all services
	$(COMPOSE_PROD) logs -f

ps: ## List running containers
	$(COMPOSE_PROD) ps

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
test: ## Run the full integration test suite
	PYTHONPATH=. pytest tests/ -v

# ---------------------------------------------------------------------------
# Security scanning (Trivy)
# ---------------------------------------------------------------------------
security-scan: ## Scan the API image for CRITICAL vulnerabilities; fail if found
	@echo "Running Trivy image scan on $(API_IMAGE)..."
	@if command -v trivy &>/dev/null; then \
	  trivy image --exit-code 1 --severity CRITICAL $(API_IMAGE); \
	else \
	  echo "Trivy not installed — running via Docker..."; \
	  docker run --rm \
	    -v /var/run/docker.sock:/var/run/docker.sock \
	    -v trivy_cache:/root/.cache/trivy \
	    aquasec/trivy:latest image --exit-code 1 --severity CRITICAL $(API_IMAGE); \
	fi
	@echo "Security scan passed — no CRITICAL vulnerabilities found."

# ---------------------------------------------------------------------------
# Verify security hardening (run after `make up`)
# ---------------------------------------------------------------------------
verify-security: ## Verify container security properties post-startup
	@echo "=== Checking API runs as non-root user ==="
	docker exec neuroflow-neuroflow-api-1 whoami
	@echo ""
	@echo "=== Checking read-only filesystem (should fail) ==="
	-docker exec neuroflow-neuroflow-api-1 touch /test 2>&1 | grep -i "read-only\|permission denied" && echo "Read-only filesystem: PASS" || true
	@echo ""
	@echo "=== Checking capabilities (should show no caps) ==="
	docker inspect neuroflow-neuroflow-api-1 | python3 -c "import sys,json; c=json.load(sys.stdin)[0]; print('CapAdd:', c['HostConfig']['CapAdd']); print('CapDrop:', c['HostConfig']['CapDrop'])"
	@echo ""
	@echo "=== Checking health status ==="
	docker inspect neuroflow-neuroflow-api-1 | python3 -c "import sys,json; h=json.load(sys.stdin)[0]['State']['Health']; print('Health Status:', h['Status'])"
