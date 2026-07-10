# =============================================================================
# Stage 1 — Node builder
# Install dependencies and build the Next.js standalone bundle.
# =============================================================================
FROM node:20-slim AS builder

WORKDIR /app

# Copy manifests first to leverage Docker layer cache
COPY package*.json ./
RUN npm ci --prefer-offline

# Copy source and build
COPY . .

# Enable standalone output so we can copy just the minimal server
# (next.config.js must have output: 'standalone')
RUN npm run build

# =============================================================================
# Stage 2 — Nginx static/SSR runtime
# Serve the Next.js standalone server behind Nginx.
# =============================================================================
FROM nginx:1.27-alpine AS runtime

LABEL maintainer="neuroflow-team" \
      version="2.0.0" \
      description="NeuroFlow Frontend — Nginx + Next.js standalone"

# Install Node so the standalone server can run
RUN apk add --no-cache nodejs

WORKDIR /app

# Copy the Next.js standalone server output
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Nginx config is mounted via Docker Compose volume; include a sensible default
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

# Start both Nginx (port 80 → proxy to Next.js :3000) and the Next.js node server
CMD sh -c "node /app/server.js &  nginx -g 'daemon off;'"
