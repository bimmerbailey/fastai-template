# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a **Full stack ai application template using Polylith Architecture** - a component-based monorepo that promotes code reusability. The architecture separates:

- **Bases** (`bases/fastai/`) - Application entry points that orchestrate components
- **Components** (`components/fastai/`) - Reusable business logic modules (database, users, items, logging, utils)
- **Projects** (`projects/api/`) - Project-specific configurations and deployments

Components can be shared across multiple bases, enabling modular development and testing.

## Development Commands

### Local Development

```bash
# Start all services (API + PostgreSQL + PgAdmin)
docker compose up

# Start in background
docker compose up -d

# View logs
docker compose logs -f api

# Stop services
docker compose down
```

The API runs on <http://localhost:8000> with hot reload enabled.

### Database Access

- **PostgreSQL**: localhost:5432 (postgres/Password123!)
- **PgAdmin**: <http://localhost:5050> (<admin@example.com>/Password123!)

### Code Quality

```bash
# Format and lint code
uv run ruff format .
uv run ruff check .

# Sort imports
uv run isort .

# Type checking
uv run pyright

# Run all code quality checks
uv run ruff format . && uv run ruff check . && uv run isort . && uv run pyright
```

### Testing

```bash
# Run all tests
uv run python -m pytest

# Run specific component tests
uv run python -m pytest test/components/fastai/users/

```

### Package Management

```bash
# Install dependencies
uv sync

# Add new dependency to workspace
uv add <package-name>

# Add dev dependency
uv add --group dev <package-name>
```

### Polylith Management

```bash

# Add new component to workspace
uv run poly create component --name {name}

# Add new base to workspace
uv run poly create base --name {name}

# Add new project to workspace
uv run poly create project --name {name}

```

## Key Technical Details

### Database Models

All models inherit from SQLModel with timezone-aware timestamps. Models are in `components/fastai/{domain}/models.py`:

- `User` - Email-based users with admin role support
- `Item` - Inventory items with decimal cost handling

### Logging & Monitoring

- Structured logging with correlation IDs via `components/fastai/logging/`
- Logfire integration for observability
- Request/response logging middleware automatically applied

### Configuration

Settings use Pydantic with environment variable support:

- Database connection strings via `DATABASE_URL`
- FastAPI settings configured in each base
- Frozen settings pattern for immutability

### Application Lifecycle

The FastAPI app uses async context managers for proper database engine management:

- Engine created on startup
- Connections properly closed on shutdown
- Middleware stack includes CORS, logging, and correlation ID

## Component Guidelines

When adding new components:

1. Create in `components/fastai/{domain}/`
2. Add core business logic in `core.py`
3. Define models in `models.py` if needed
4. Register in root `pyproject.toml` under `[tool.polylith.bricks]`
5. Add to project dependencies in `projects/api/pyproject.toml`
6. Create corresponding tests in `test/components/fastai/{domain}/`

## Database Migrations

Alembic is configured but no migrations exist yet. When adding migrations:

```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```
