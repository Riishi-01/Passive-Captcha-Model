# Multi-stage Production Dockerfile for Backend
# Optimized for Render.com deployment

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-render.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-render.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Copy ML models and ensure they exist
COPY models/ /app/models/
RUN test -f models/passive_captcha_rf.pkl || echo "Warning: ML model not found"

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/uploads /app/tmp && \
    chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV WEB_CONCURRENCY=2
ENV WORKER_TIMEOUT=120

# Health check (Render-compatible)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5003}/health || exit 1

# Switch to non-root user
USER appuser

# Expose port (Render will override with PORT env var)
EXPOSE 5003

# Production entrypoint
CMD ["python", "main.py"]