# Multi-stage build for mdd-stock-mcp HTTP transport mode
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy project metadata first for layer caching
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies and project into system Python
RUN uv pip install --system .

# ---- Final stage ----
FROM python:3.11-slim

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/mdd-stock-mcp /usr/local/bin/mdd-stock-mcp

EXPOSE 8000

# Honor $PORT (Render/Cloud Run inject this); fall back to 8000 for local docker run.
CMD ["sh", "-c", "mdd-stock-mcp --transport http --host 0.0.0.0 --port ${PORT:-8000}"]
