# =============================================================================
# AI Companion Service - Docker Management Makefile
# =============================================================================
# Simplifies common Docker operations for development and production
#
# Usage:
#   make help           - Show all available commands
#   make dev            - Start development environment
#   make prod           - Start production environment
#   make stop           - Stop all services
#   make logs           - View logs
# =============================================================================

.PHONY: help dev prod stop restart clean logs shell db-shell test build backup restore health status

# Default target
.DEFAULT_GOAL := help

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
RESET  := \033[0m

# Variables
# Prefer Docker Compose v2 (`docker compose`). Docker Compose v1 (`docker-compose`)
# is incompatible with newer Docker Engine versions (e.g., can throw KeyError: 'ContainerConfig').
COMPOSE_DEV := docker compose -f docker-compose.dev.yml
COMPOSE_PROD := docker compose
SERVICE_NAME := aiservice
DB_SERVICE := postgres

# =============================================================================
# Help Target
# =============================================================================
help: ## Show this help message
	@echo "$(GREEN)AI Companion Service - Docker Commands$(RESET)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# Development Environment
# =============================================================================
dev: ## Start development environment with hot-reload
	@echo "$(GREEN)Starting development environment...$(RESET)"
	$(COMPOSE_DEV) up -d
	@echo "$(GREEN)✓ Development environment is running$(RESET)"
	@echo ""
	@echo "$(YELLOW)📡 API Services:$(RESET)"
	@echo "  • API:        http://localhost:8000"
	@echo "  • API Docs:   http://localhost:8000/docs"
	@echo "  • Chat UI:    http://localhost:8000/ui"
	@echo ""
	@echo "$(YELLOW)🎨 Database UI (Adminer):$(RESET)"
	@echo "  • URL:        http://localhost:8080"
	@echo "  • Server:     postgres"
	@echo "  • Username:   postgres"
	@echo "  • Password:   changeme"
	@echo "  • Database:   ai_companion"
	@echo ""
	@echo "$(YELLOW)🔧 Direct Access:$(RESET)"
	@echo "  • Database:   localhost:5433"
	@echo "  • Redis:      localhost:6379"
	@echo ""

dev-build: ## Build and start development environment
	@echo "$(GREEN)Building development environment...$(RESET)"
	$(COMPOSE_DEV) build --no-cache
	$(COMPOSE_DEV) up -d
	@echo "$(GREEN)✓ Development environment is running$(RESET)"

dev-adminer: ## Start development with Adminer database UI
	@echo "$(GREEN)Starting development with Adminer...$(RESET)"
	$(COMPOSE_DEV) --profile with-adminer up -d
	@echo "$(GREEN)✓ Development environment is running$(RESET)"
	@echo "API: http://localhost:8000"
	@echo "Adminer: http://localhost:8080"

# =============================================================================
# Production Environment
# =============================================================================
prod: ## Start production environment
	@echo "$(GREEN)Starting production environment...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found!$(RESET)"; \
		echo "$(YELLOW)Copy ENV_EXAMPLE.txt to .env and configure it$(RESET)"; \
		exit 1; \
	fi
	$(COMPOSE_PROD) up -d
	@echo "$(GREEN)✓ Production environment is running$(RESET)"
	@echo "API: http://localhost:8000"

prod-build: ## Build and start production environment
	@echo "$(GREEN)Building production environment...$(RESET)"
	$(COMPOSE_PROD) build --no-cache
	$(COMPOSE_PROD) up -d
	@echo "$(GREEN)✓ Production environment is running$(RESET)"

prod-nginx: ## Start production with Nginx reverse proxy
	@echo "$(GREEN)Starting production with Nginx...$(RESET)"
	$(COMPOSE_PROD) --profile with-nginx up -d
	@echo "$(GREEN)✓ Production environment is running with Nginx$(RESET)"
	@echo "API: http://localhost:80"

# =============================================================================
# Service Management
# =============================================================================
stop: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(RESET)"
	$(COMPOSE_DEV) down 2>/dev/null || true
	$(COMPOSE_PROD) down 2>/dev/null || true
	@echo "$(GREEN)✓ All services stopped$(RESET)"

restart-dev: stop dev ## Restart development environment

restart-prod: stop prod ## Restart production environment

clean: ## Stop and remove all containers, networks, and volumes
	@echo "$(RED)WARNING: This will remove all data!$(RESET)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE_DEV) down -v 2>/dev/null || true; \
		$(COMPOSE_PROD) down -v 2>/dev/null || true; \
		echo "$(GREEN)✓ Cleaned up all containers and volumes$(RESET)"; \
	fi

# =============================================================================
# Logs and Debugging
# =============================================================================
logs: ## View logs from all services
	$(COMPOSE_DEV) logs -f 2>/dev/null || $(COMPOSE_PROD) logs -f

logs-api: ## View logs from API service only
	$(COMPOSE_DEV) logs -f $(SERVICE_NAME) 2>/dev/null || $(COMPOSE_PROD) logs -f $(SERVICE_NAME)

logs-db: ## View logs from database service only
	$(COMPOSE_DEV) logs -f $(DB_SERVICE) 2>/dev/null || $(COMPOSE_PROD) logs -f $(DB_SERVICE)

shell: ## Open shell in API container
	@$(COMPOSE_DEV) exec $(SERVICE_NAME) /bin/bash 2>/dev/null || $(COMPOSE_PROD) exec $(SERVICE_NAME) /bin/bash

db-shell: ## Open PostgreSQL shell
	@$(COMPOSE_DEV) exec $(DB_SERVICE) psql -U postgres -d ai_companion_dev 2>/dev/null || \
	$(COMPOSE_PROD) exec $(DB_SERVICE) psql -U postgres -d ai_companion

# =============================================================================
# Health and Status
# =============================================================================
status: ## Show status of all services
	@echo "$(GREEN)Service Status:$(RESET)"
	@$(COMPOSE_DEV) ps 2>/dev/null || $(COMPOSE_PROD) ps

health: ## Check health of all services
	@echo "$(GREEN)Health Check:$(RESET)"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "$(RED)API not responding$(RESET)"

# =============================================================================
# Database Operations
# =============================================================================
db-migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(RESET)"
	@$(COMPOSE_DEV) exec $(SERVICE_NAME) alembic upgrade head 2>/dev/null || \
	$(COMPOSE_PROD) exec $(SERVICE_NAME) alembic upgrade head
	@echo "$(GREEN)✓ Migrations completed$(RESET)"

db-backup: ## Backup database
	@echo "$(GREEN)Creating database backup...$(RESET)"
	@mkdir -p ./backups
	@$(COMPOSE_DEV) exec -T $(DB_SERVICE) pg_dump -U postgres -d ai_companion_dev > \
		./backups/backup_dev_$(shell date +%Y%m%d_%H%M%S).sql 2>/dev/null || \
	$(COMPOSE_PROD) exec -T $(DB_SERVICE) pg_dump -U postgres -d ai_companion > \
		./backups/backup_prod_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Backup created in ./backups/$(RESET)"

db-restore: ## Restore database from backup (usage: make db-restore FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: FILE parameter required$(RESET)"; \
		echo "Usage: make db-restore FILE=backups/backup.sql"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Restoring database from $(FILE)...$(RESET)"
	@$(COMPOSE_DEV) exec -T $(DB_SERVICE) psql -U postgres -d ai_companion_dev < $(FILE) 2>/dev/null || \
	$(COMPOSE_PROD) exec -T $(DB_SERVICE) psql -U postgres -d ai_companion < $(FILE)
	@echo "$(GREEN)✓ Database restored$(RESET)"

# =============================================================================
# Testing
# =============================================================================
test: ## Run tests in container
	@echo "$(GREEN)Running tests...$(RESET)"
	$(COMPOSE_DEV) exec $(SERVICE_NAME) pytest tests/ -v

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	$(COMPOSE_DEV) exec $(SERVICE_NAME) pytest tests/ --cov=app --cov-report=html

# =============================================================================
# Build and Push
# =============================================================================
build: ## Build Docker images
	@echo "$(GREEN)Building Docker images...$(RESET)"
	docker build -t ai-companion:latest \
		--build-arg BUILD_DATE=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ") \
		--build-arg VERSION=1.0.0 \
		--build-arg VCS_REF=$(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
		.
	@echo "$(GREEN)✓ Build completed$(RESET)"

push: ## Push Docker image to registry (requires DOCKER_REGISTRY env var)
	@if [ -z "$(DOCKER_REGISTRY)" ]; then \
		echo "$(RED)Error: DOCKER_REGISTRY not set$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Pushing to $(DOCKER_REGISTRY)...$(RESET)"
	docker tag ai-companion:latest $(DOCKER_REGISTRY)/ai-companion:latest
	docker push $(DOCKER_REGISTRY)/ai-companion:latest
	@echo "$(GREEN)✓ Push completed$(RESET)"

# =============================================================================
# Maintenance
# =============================================================================
update: ## Update all services
	@echo "$(GREEN)Updating services...$(RESET)"
	git pull
	$(COMPOSE_DEV) pull 2>/dev/null || $(COMPOSE_PROD) pull
	$(COMPOSE_DEV) build 2>/dev/null || $(COMPOSE_PROD) build
	@echo "$(GREEN)✓ Update completed$(RESET)"

prune: ## Remove unused Docker resources
	@echo "$(YELLOW)Cleaning up Docker resources...$(RESET)"
	docker system prune -f
	@echo "$(GREEN)✓ Cleanup completed$(RESET)"

# =============================================================================
# Quick Commands
# =============================================================================
up: dev ## Alias for 'make dev'

down: stop ## Alias for 'make stop'

rebuild: clean dev-build ## Clean and rebuild everything

