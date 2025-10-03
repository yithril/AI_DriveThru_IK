# syntax=docker/dockerfile:1

# Stage 1: Build dependencies
FROM python:3.11 as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Poetry
RUN pip install poetry

# Copy Poetry files first for better caching
COPY pyproject.toml ./

# Install dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/poetry \
    poetry config virtualenvs.create false \
    && poetry install --only=main

# Stage 2: Final runtime image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy only the essential Python packages (not Poetry or build tools)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "main.py"]

