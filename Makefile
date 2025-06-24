.PHONY: help install dev up down logs clean format lint check test build

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Package Management:"
	@echo "  install                    - Install dependencies"
	@echo ""
	@echo "Development:"
	@echo "  dev                        - Start development environment"
	@echo "  down                       - Stop all services"
	@echo "  logs                       - View service logs (SERVICES=service_name)"
	@echo "  clean                      - Clean up containers and volumes"
	@echo "  exec                       - Execute command in container (SERVICE=name CMD=\"command\")"
	@echo ""
	@echo "Code Quality:"
	@echo "  format                     - Format and sort imports"
	@echo "  lint                       - Run all code quality checks (format + type + polylith)"
	@echo "  check                      - Run type checking only"
	@echo ""
	@echo "Testing:"
	@echo "  test                       - Run all tests"
	@echo "  test-watch                 - Run tests in watch mode"
	@echo "  test-coverage              - Run tests with coverage report"
	@echo "  test-fast                  - Run tests until first failure"
	@echo ""
	@echo "Polylith:"
	@echo "  poly-info                  - Show workspace information"
	@echo "  poly-check                 - Check workspace consistency"
	@echo "  poly-diff                  - Show workspace changes"
	@echo "  poly-libs                  - Show library dependencies"
	@echo "  poly-sync                  - Sync workspace"
	@echo "  poly-deps                  - Show dependencies"
	@echo "  poly-create-component      - Create component (NAME=component_name)"
	@echo "  poly-create-base           - Create base (NAME=base_name)"
	@echo "  poly-create-project        - Create project (NAME=project_name)"
	@echo ""
	@echo "Database:"
	@echo "  migrate-create             - Create migration (message=\"description\")"
	@echo "  migrate-up                 - Run migrations"

# Package management
install:
	uv sync --all-groups --all-extras

# Development environment
dev:
	docker compose up api

down:
	docker compose down

logs:
	docker compose logs -f $(SERVICES)

clean:
	docker compose down -v --remove-orphans

# Code quality
format:
	uv run ruff format .
	uv run ruff check .
	uv run isort .

lint:
	uv run ruff format . 
	uv run ruff check .
	uv run isort . 
	uv run pyright
	uv run poly check --strict

check:
	uv run pyright

# Test targets
.PHONY: test test-watch test-coverage test-fast

test:
	uv run pytest test -v $(PYTEST_ARGS)

test-watch:
	uv run pytest test -v --watch $(PYTEST_ARGS)

test-coverage:
	uv run pytest test -v --cov --cov-report=html --cov-report=term $(PYTEST_ARGS)

test-fast:
	uv run pytest test -x $(PYTEST_ARGS)

# Polylith commands
# Python Polylith targets
.PHONY: poly-info poly-check poly-diff poly-libs poly-sync poly-deps poly-create-component poly-create-base poly-create-project

poly-info:
	uv run poly info

poly-check:
	uv run poly check --strict

poly-diff:
	uv run poly diff

poly-libs:
	uv run poly libs

poly-sync:
	uv run poly sync

poly-deps:
	uv run poly deps

poly-create-component:
	@if [ -z "$(NAME)" ]; then echo "Error: NAME is required. Usage: make poly-create-component NAME=component_name"; exit 1; fi
	uv run poly create component --name $(NAME)

poly-create-base:
	@if [ -z "$(NAME)" ]; then echo "Error: NAME is required. Usage: make poly-create-base NAME=base_name"; exit 1; fi
	uv run poly create base --name $(NAME)

poly-create-project:
	@if [ -z "$(NAME)" ]; then echo "Error: NAME is required. Usage: make poly-create-project NAME=project_name"; exit 1; fi
	uv run poly create project --name $(NAME)

# Database migrations
migrate-create:
	uv run alembic revision --autogenerate -m "$(message)"

migrate-up:
	uv run alembic upgrade head

# Database and utility targets
.PHONY: exec

# Generic exec command - Usage: make exec SERVICE=container_name CMD="command to run"
exec:
	@if [ -z "$(SERVICE)" ]; then echo "Error: SERVICE is required. Usage: make exec SERVICE=container_name CMD=\"command\""; exit 1; fi
	@if [ -z "$(CMD)" ]; then echo "Error: CMD is required. Usage: make exec SERVICE=container_name CMD=\"command\""; exit 1; fi
	docker compose exec -it $(SERVICE) $(CMD)
