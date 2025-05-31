FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS base

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR "/src"

COPY pyproject.toml uv.lock README.md ./
# Install dependencies
RUN uv sync --locked --no-install-project --no-dev

COPY ./bases ./bases
COPY ./components ./components
COPY ./projects ./projects
COPY ./test ./test

FROM base AS dev
 
EXPOSE 8000
ENTRYPOINT ["uv", "run"]
CMD ["uvicorn", "fastai.api:init_api", "--host", "0.0.0.0", \
     "--port", "8000", "--reload", "--no-access-log", "--factory"]