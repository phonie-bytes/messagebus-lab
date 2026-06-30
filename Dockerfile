# Stage 1: Build dependencies using uv
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy the entire project context (respects .dockerignore)
COPY . .

# Install dependencies and our app package
RUN uv sync --no-dev

# Stage 2: Final production image
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user for security
RUN useradd -m appuser
USER appuser

# Copy the installed virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy our actual application code
COPY src ./src

# Tell Python to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV ENVIRONMENT="production"

# Run the async consumer by default when the container starts
CMD ["messagebus", "receive-async"]