# =============================================================================
# Multi-stage Docker build for AI Companion Service
# =============================================================================
# Build: docker build -t ai-companion:latest .
# Run:   docker-compose up -d
# =============================================================================

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set build arguments for versioning
ARG BUILD_DATE
ARG VERSION=1.0.0
ARG VCS_REF

# Add labels for better container management
LABEL org.opencontainers.image.title="AI Companion Service"
LABEL org.opencontainers.image.description="Intelligent AI companion with memory and personality"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL maintainer="AI Companion Team"

WORKDIR /build

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Pre-download the embedding model to cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# =============================================================================
# Stage 2: Runtime stage
# =============================================================================
FROM python:3.11-slim

# Set build arguments
ARG BUILD_DATE
ARG VERSION=1.0.0
ARG VCS_REF

# Add labels
LABEL org.opencontainers.image.title="AI Companion Service"
LABEL org.opencontainers.image.description="Intelligent AI companion with memory and personality"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL maintainer="AI Companion Team"

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser -g 1000 && \
    useradd -r -u 1000 -g appuser -m -s /sbin/nologin appuser

# Copy Python packages from builder to appuser's directory
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --from=builder --chown=appuser:appuser /root/.cache /home/appuser/.cache

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser app/ /app/app/
COPY --chown=appuser:appuser alembic.ini /app/
COPY --chown=appuser:appuser migrations/ /app/migrations/
COPY --chown=appuser:appuser frontend/ /app/frontend/

# Copy entrypoint script
COPY --chown=appuser:appuser docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Add local pip packages to PATH
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

