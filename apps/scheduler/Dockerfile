# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy shared package first (for local dependency)
COPY shared/python/pr_review_shared /shared/python/pr_review_shared

# Copy application code
COPY apps/scheduler/pyproject.toml apps/scheduler/

# Install dependencies
RUN pip install --no-cache-dir /shared/python/pr_review_shared
RUN pip install --no-cache-dir /app/apps/scheduler

# Stage 2: Runtime
FROM python:3.11-slim as runtime

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY apps/scheduler/src /app/src

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Run the scheduler
CMD ["python", "-m", "pr_review_scheduler.main"]
