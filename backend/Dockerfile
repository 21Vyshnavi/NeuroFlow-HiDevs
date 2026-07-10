# =============================================================================
# Stage 1 — dependency builder
# Install all Python packages here so the runtime image stays minimal.
# =============================================================================
FROM python:3.11-slim AS deps

WORKDIR /app

# Install build-time OS deps (needed by some wheels, not needed at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2 — minimal runtime
# Non-root user, curl for health probe, nothing else.
# =============================================================================
FROM python:3.11-slim AS runtime

LABEL maintainer="neuroflow-team" \
      version="2.0.0" \
      description="NeuroFlow API — production runtime image"

# Install only runtime OS deps (curl for HEALTHCHECK, libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user / group
RUN groupadd -r neuroflow && useradd -r -g neuroflow -d /app -s /sbin/nologin neuroflow

WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source
COPY --chown=neuroflow:neuroflow . .

# Drop to non-root
USER neuroflow

EXPOSE 8000

# Health probe — hits /health every 30 s; start-period gives FastAPI time to boot
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 4 workers for production; honour PORT env var via shell form so Docker can override
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips=*"]
