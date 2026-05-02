ARG PYTHON_VERSION=3.13

FROM python:$PYTHON_VERSION-bookworm AS uv

ENV  PYTHONUNBUFFERED=1 \
     UV_COMPILE_BYTECODE=1 \
     UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:0.10.11 /uv /uvx /bin/

FROM uv AS base

# OpenCV (cv2) runtime dependencies required by docling-ibm-models
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR "/src"

COPY pyproject.toml uv.lock README.md ./
# Install dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package worker --frozen --no-install-project --no-install-workspace --no-dev

COPY ./bases ./bases
COPY ./components ./components
COPY ./projects ./projects

FROM base AS dev

# Use symlinks instead of copies so volume-mounted source changes
# are reflected immediately without reinstalling.
ENV UV_LINK_MODE=symlink

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
     uv sync --package worker --frozen

ENTRYPOINT ["uv", "run"]
CMD ["faststream", "run", "fastai.worker:create_app", "--reload", "--factory"]

FROM base AS builder

RUN uv venv /opt/venv
# Use the virtual environment automatically
ENV VIRTUAL_ENV=/opt/venv

RUN --mount=type=cache,target=/root/.cache/uv \
    uv build --package worker --wheel .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv export --package worker --no-emit-package worker \
    --format requirements-txt > requirements.txt

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install dist/*.whl
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements.txt

FROM python:$PYTHON_VERSION-slim-bookworm AS prod

# OpenCV (cv2) runtime dependencies required by docling-ibm-models
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv

COPY --from=builder /opt/venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENTRYPOINT ["faststream"]
CMD ["run", "fastai.worker:create_app", "--factory"]
