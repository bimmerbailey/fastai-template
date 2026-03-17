ARG PYTHON_VERSION=3.13

FROM python:$PYTHON_VERSION-bookworm AS uv

ENV  PYTHONUNBUFFERED=1 \
     UV_COMPILE_BYTECODE=1 \
     UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:0.10.11 /uv /uvx /bin/

FROM uv AS base

WORKDIR "/src"

COPY pyproject.toml uv.lock README.md ./
# Install dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package api --frozen --no-install-project --no-install-workspace --no-dev

COPY ./bases ./bases
COPY ./components ./components
COPY ./projects ./projects
COPY ./test ./test

FROM base AS dev

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
     uv sync --package api --frozen
 
EXPOSE 8000
ENTRYPOINT ["uv", "run"]
CMD ["uvicorn", "fastai.api:init_api", "--host", "0.0.0.0", \
     "--port", "8000", "--reload", "--no-access-log", "--factory"]

FROM base AS builder

RUN uv venv /opt/venv
# Use the virtual environment automatically
ENV VIRTUAL_ENV=/opt/venv

RUN --mount=type=cache,target=/root/.cache/uv \
    uv build --package api --wheel .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv export --package api --no-emit-package api \
    --format requirements-txt > requirements.txt

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install dist/*.whl
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements.txt

FROM python:$PYTHON_VERSION-slim-bookworm AS prod

ENV VIRTUAL_ENV=/opt/venv

COPY --from=builder /opt/venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

EXPOSE 80
ENTRYPOINT ["gunicorn"]
CMD ["-k", "uvicorn.workers.UvicornWorker", \
    "--bind=0.0.0.0:80", "--access-logfile", "-", "fastai.api:init_api()"]