# Stage 1: Builder
FROM dhi.io/python:3.14-alpine3.23-dev AS builder

WORKDIR /app

# Create venv and add to PATH
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy shared package first (for local dependency)
COPY shared/python/pr_review_shared /shared/python/pr_review_shared

# Copy application code
COPY apps/web-be/pyproject.toml apps/web-be/
COPY apps/web-be/src apps/web-be/src/

# Install dependencies
RUN pip install --no-cache-dir /shared/python/pr_review_shared
RUN pip install --no-cache-dir /app/apps/web-be

# Stage 2: Runtime
FROM dhi.io/python:3.14-alpine3.23

WORKDIR /app

# Copy installed packages from builder and add venv to PATH
COPY --from=builder /app/venv /app/venv
COPY apps/web-be/alembic.ini /app/
COPY apps/web-be/alembic /app/alembic

ENV PATH="/app/venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Run the application
CMD ["uvicorn", "pr_review_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
