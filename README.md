# FastAI Template

A full-stack AI application template built on **Polylith Architecture** — a component-based monorepo that promotes code
reusability across multiple applications.

## Features

- **Polylith monorepo** — modular components shared across bases and projects
- **FastAPI** with async/await, automatic OpenAPI docs, and dependency injection
- **PostgreSQL** with async SQLAlchemy, SQLModel ORM, and Alembic migrations
- **JWT authentication** with refresh tokens, account lockout, and Argon2id hashing
- **AI agent system** powered by Pydantic AI with OpenAI, Anthropic, and Ollama support
- **Structured logging** with structlog, Logfire observability, and correlation IDs
- **Docker Compose** development environment with hot reload

## Quick Start

```bash
git clone <repo-url> && cd fastai-template

# Install dependencies
make install

# Start everything (API + Postgres + PgAdmin)
make dev
```

The API is available at [http://localhost:8000](http://localhost:8000) with interactive docs at `/docs`.

## Prerequisites

- [Python 3.13+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) — fast Python package manager
- [Docker](https://www.docker.com/) and Docker Compose

## Configuration

This project uses a **two-file environment variable pattern**:

| File          | Committed       | Purpose                                    |
|---------------|-----------------|--------------------------------------------|
| `example.env` | Yes             | Dev-safe defaults that work out of the box |
| `.env`        | No (gitignored) | Your local overrides and secrets           |

### Setup

For local development, the defaults in `example.env` are loaded automatically — no action needed. To override any value,
create a `.env` file:

```bash
cp example.env .env
# Edit .env with your values
```

Pydantic Settings loads `.env` first, then falls back to `example.env`. Environment variables set in the shell take
highest precedence.

### Variables

| Variable                   | Default                     | Description                            |
|----------------------------|-----------------------------|----------------------------------------|
| `FASTAI_POSTGRES_HOSTNAME` | `localhost`                 | Database host (`postgres` in Docker)   |
| `FASTAI_POSTGRES_PORT`     | `5432`                      | Database port                          |
| `FASTAI_POSTGRES_NAME`     | `fastai`                    | Database name                          |
| `FASTAI_POSTGRES_USER`     | `postgres`                  | Database user                          |
| `FASTAI_POSTGRES_PASSWORD` | `Password123!`              | Database password                      |
| `FASTAI_AUTH_SECRET_KEY`   | dev placeholder             | JWT signing key (change in production) |
| `FASTAI_AGENT_MODEL`       | `ollama:llama3.2:3b`        | AI model in `provider:model` format    |
| `OLLAMA_BASE_URL`          | `http://localhost:11434/v1` | Ollama API endpoint                    |

All settings classes inherit from a shared `FastAISettings` base (`components/fastai/utils/settings.py`) that configures
the two-file loading. When Docker Compose starts the API service, it loads `example.env`, then `.env` (if present), and
finally applies inline overrides like `FASTAI_POSTGRES_HOSTNAME=postgres` for container networking.

## Architecture

This project follows the [Polylith](https://polylith.gitbook.io/) architecture:

```
fastai-template/
├── bases/fastai/api/           # Application entry points
│   └── core.py                 #   FastAPI app initialization
├── components/fastai/          # Reusable business logic
│   ├── auth/                   #   JWT auth, tokens, password hashing
│   ├── agents/                 #   Pydantic AI agent system
│   ├── chats/                  #   Chat and conversation models
│   ├── database/               #   Engine, sessions, health checks
│   ├── items/                  #   Item CRUD operations
│   ├── logger/                 #   Structured logging setup
│   ├── users/                  #   User management
│   ├── utils/                  #   Shared settings, timestamps, fields
│   ├── api_v1/                 #   Public API v1 routes
│   └── admin_v1/               #   Admin management routes
├── projects/api/               # Deployment configuration
│   ├── Dockerfile              #   Multi-stage build
│   └── pyproject.toml          #   Project-specific dependencies
├── example.env                 # Committed dev defaults
├── compose.yml                 # Docker Compose services
└── test/                       # Tests mirroring component structure
```

**Bases** are application entry points that wire together components. **Components** contain reusable business logic —
each with its own models, schemas, and core logic. **Projects** define how bases and components are packaged for
deployment.

## Development

### Common Commands

```bash
make dev              # Start Docker environment (API + Postgres + PgAdmin)
make dev-local        # Run API locally (reads .env)
make down             # Stop all services
make logs             # View logs (SERVICES=api for specific service)
make clean            # Remove containers and volumes
```

### Code Quality

```bash
make format           # Format code (ruff + isort)
make lint             # Run all checks (format, types, polylith)
make type-check       # Pyright only
```

### Testing

```bash
make test             # Run all tests
make test-fast        # Stop at first failure
make test-watch       # Watch mode
make test-coverage    # Generate coverage report
```

Run specific component tests directly:

```bash
uv run pytest test/components/fastai/users/ -v
```

Integration tests that require a running database are marked with `@pytest.mark.integration`.

### Database

- **PostgreSQL**: localhost:5432
- **PgAdmin**: [http://localhost:5050](http://localhost:5050) (admin@example.com / Password123!)

```bash
make migrate-create message="add users table"
make migrate-up
```

### Adding Components

```bash
make poly-create-component NAME=notifications
```

Then follow the structure: add `core.py` for logic, `models.py` for database models, register in the root
`pyproject.toml` under `[tool.polylith.bricks]`, and add to `projects/api/pyproject.toml`.

## Tech Stack

| Layer            | Technology                              |
|------------------|-----------------------------------------|
| Language         | Python 3.13+                            |
| Web framework    | FastAPI + Uvicorn                       |
| ORM              | SQLModel + SQLAlchemy (async)           |
| Database         | PostgreSQL 17 + asyncpg                 |
| Auth             | JWT (joserfc) + Argon2id (pwdlib)       |
| AI               | Pydantic AI (OpenAI, Anthropic, Ollama) |
| Observability    | structlog + Logfire                     |
| Package manager  | uv                                      |
| Type checking    | Pyright                                 |
| Linting          | Ruff + isort                            |
| Architecture     | Polylith                                |
| Containerization | Docker Compose                          |
