# Stage 1: Builder
FROM python:3.14-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy shared package first (for local dependency)
COPY shared/python/pr_review_shared /shared/python/pr_review_shared

# Copy application code
COPY apps/web-be/pyproject.toml apps/web-be/
COPY apps/web-be/src apps/web-be/src/

# Install dependencies
RUN pip install --no-cache-dir /shared/python/pr_review_shared
RUN pip install --no-cache-dir /app/apps/web-be

# Stage 2: Runtime
FROM python:3.14-slim as runtime

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY apps/web-be/src /app/src
COPY apps/web-be/alembic.ini /app/
COPY apps/web-be/alembic /app/alembic

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Run the application
CMD ["uvicorn", "pr_review_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
