# app/Dockerfile
FROM python:3.12-slim-bookworm

# Install 'uv'
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment Configuration
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # Set PATH to use 'uv', 'uvicorn', etc. directly
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Security: Create user *before* copying files
# Create the user, then ensure they own the /app directory
RUN useradd -m -u 1000 appuser && chown appuser:appuser /app

# Switch to non-root user
USER appuser

# Install Dependencies (Cached Layer)
# We use --chown so 'appuser' owns lockfiles and .venv created by uv
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Sync dependencies
# --frozen: strictly use lock file
# --no-install-project: strictly install deps, not the app itself (yet)
RUN uv sync --frozen --no-install-project

# Copy Application Code
# Ensure appuser owns the source code
COPY --chown=appuser:appuser . .

# FastAPI/Uvicorn Specifics
# FastAPI runs on 8000 by default
EXPOSE 8000

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Run Application
CMD ["uv", "run", "uvicorn", "coach.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]