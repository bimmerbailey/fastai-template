# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a **Full stack ai application template using Polylith Architecture** - a component-based monorepo that promotes code reusability. The architecture separates:

- **Bases** (`bases/fastai/`) - Application entry points that orchestrate components
- **Components** (`components/fastai/`) - Reusable business logic modules (database, users, items, logging, utils)
- **Projects** (`projects/api/`) - Project-specific configurations and deployments

Components can be shared across multiple bases, enabling modular development and testing.

## Development Commands

Use `make help` to see all available commands. Key commands:

### Local Development

```bash
# Start development environment
make dev

# Stop all services  
make down

# View logs (optionally specify SERVICES=service_name)
make logs

# Clean up containers and volumes
make clean

# Execute commands in containers
make exec SERVICE=api CMD="bash"
```

The API runs on <http://localhost:8000> with hot reload enabled.

### Database Access

- **PostgreSQL**: localhost:5432 (postgres/Password123!)
- **PgAdmin**: <http://localhost:5050> (<admin@example.com>/Password123!)

### Code Quality

```bash
# Format code and sort imports
make format

# Run all code quality checks (format + type check + polylith check)
make lint

# Type checking only
make check
```

### Testing

```bash
# Run all tests
make test

# Run tests in watch mode
make test-watch

# Run tests with coverage report
make test-coverage

# Run tests until first failure
make test-fast

# Run specific component tests
uv run pytest test/components/fastai/users/ -v
```

### Package Management

```bash
# Install all dependencies
make install

# Add new dependency to workspace
uv add <package-name>

# Add dev dependency
uv add --group dev <package-name>
```

### Polylith Management

```bash
# Show workspace information
make poly-info

# Check workspace consistency
make poly-check

# Show workspace changes
make poly-diff

# Create new component
make poly-create-component NAME=component_name

# Create new base
make poly-create-base NAME=base_name

# Create new project
make poly-create-project NAME=project_name
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
# Create migration
make migrate-create message="description"

# Run migrations
make migrate-up
```

## AI Integration

The template includes Pydantic AI integration for building AI applications:

- **pydantic-ai-slim** with OpenAI and Logfire support
- **fastmcp** for Model Context Protocol integration
- Structured logging optimized for AI/ML observability

## Technology Stack

- **Python 3.13+** with modern async/await patterns
- **FastAPI** with automatic OpenAPI documentation
- **SQLModel** for database models with Pydantic integration
- **PostgreSQL** with async connection pooling
- **uv** for fast dependency management
- **Logfire** for observability and monitoring
- **Docker Compose** for local development

## Important Notes

- All timestamps are timezone-aware using UTC
- Database models use SQLModel with automatic created_at/updated_at fields
- Correlation IDs are automatically added to requests for tracing
- The application uses async context managers for proper resource cleanup


## Development Memories

- Make sure all function arguments have types
- Integration tests should be marked "integration" and should not contain mocks
- Integration test should be completed and passing before doing mocked tests
- Always use absolute paths NEVER relative paths
