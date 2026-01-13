.PHONY: help build up down logs clean dev restart stop test seed seed-complex benchmarks e2e-test load init-db

help:
	@echo "MySQLens - Makefile Commands"
	@echo "===================================="
	@echo ""
	@echo "Docker Commands:"
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start services in production mode"
	@echo "  make down         - Stop services"
	@echo "  make logs         - View logs"
	@echo "  make clean        - Remove containers and volumes"
	@echo "  make dev          - Start services in development mode"
	@echo "  make restart      - Restart services"
	@echo "  make stop         - Stop services (without removing)"
	@echo ""
	@echo "Testing & Development:"
	@echo "  make test         - Test Ollama integration"
	@echo "  make seed         - Seed demo data (1K users, 5K orders)"
	@echo "  make seed-complex - Seed complex demo data (larger dataset)"
	@echo "  make benchmarks   - Run LLM benchmarks against golden dataset"
	@echo "  make e2e-test     - Run end-to-end tests"
	@echo "  make load         - Start continuous load generator"
	@echo "  make init-db      - Initialize MySQLens schema"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v
	docker system prune -f

dev:
	docker compose -f docker-compose.dev.yml up

restart:
	docker compose restart

stop:
	docker compose stop

test:
	docker compose exec mysqlens-api python test_ollama.py

# ============================================
# Seed & Testing Commands
# ============================================

seed:
	@echo "Seeding demo data..."
	python scripts/seed/seed_data.py

seed-complex:
	@echo "Seeding complex demo data..."
	python scripts/seed/seed_complex.py

benchmarks:
	@echo "Running LLM benchmarks..."
	python scripts/run_benchmarks.py

e2e-test:
	@echo "Running end-to-end tests..."
	python scripts/test_complete_optimization_flow.py

load:
	@echo "Starting load generator (Ctrl+C to stop)..."
	python scripts/load/generate_load.py

init-db:
	@echo "Initializing MySQLens schema..."
	@echo "Run: mysql -u root -p < scripts/seed/init.sql"

