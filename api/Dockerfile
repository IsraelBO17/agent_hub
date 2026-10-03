# Standard §19: multi-stage, both images pinned by digest (update monthly), non-root.
# Build for arm64: `make image` (docker build --platform linux/arm64).
# One image, every role: the API (default), the worker (`python -m app.worker`), and
# migrations (`alembic upgrade head`, run with the direct database URL).

FROM ghcr.io/astral-sh/uv:0.12.22-python3.12-trixie-slim@sha256:1ff88987c417eb9c1ebcf6e8dc728d26b61f538d3010bf4c18f33fcc1a67c6b6 AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1 UV_PYTHON_DOWNLOADS=0
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project
COPY pyproject.toml uv.lock ./
COPY src ./src
# Non-editable: the runtime image needs only .venv, not the source tree.
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-editable

FROM python:3.12-slim-trixie@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
RUN groupadd --system --gid 999 app && useradd --system --gid 999 --uid 999 --no-create-home app
WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app alembic.ini openapi.yaml ./
COPY --chown=app:app migrations ./migrations
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
CMD ["python", "-m", "app.serve"]
