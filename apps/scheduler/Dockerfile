# Stage 1: Builder
FROM dhi.io/python:3.14-alpine3.23-dev AS builder

WORKDIR /app

# Create venv and add to PATH
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy shared package first (for local dependency)
COPY shared/python/pr_review_shared /shared/python/pr_review_shared

# Copy application code
COPY apps/scheduler/pyproject.toml apps/scheduler/
COPY apps/scheduler/src apps/scheduler/src/

# Install dependencies
RUN pip install --no-cache-dir /shared/python/pr_review_shared
RUN pip install --no-cache-dir /app/apps/scheduler

# Stage 2: Runtime
FROM dhi.io/python:3.14-alpine3.23

WORKDIR /app

# Copy installed packages from builder and add venv to PATH
COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Run the scheduler
CMD ["python", "-m", "pr_review_scheduler.main"]
