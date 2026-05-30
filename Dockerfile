FROM python:3.11-slim

# Install uv via pip (no external registry pull required).
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy project metadata first for layer caching.
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the project and its dependencies into the system Python.
RUN uv pip install --system .

EXPOSE 8000

# Honor $PORT (Render/Cloud Run inject this); fall back to 8000 for local docker run.
CMD ["sh", "-c", "mdd-stock-mcp --transport http --host 0.0.0.0 --port ${PORT:-8000}"]
