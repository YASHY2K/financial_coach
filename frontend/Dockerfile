FROM node:23-alpine

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN addgroup -g 1001 -S appuser && \
    adduser -S -D -H -u 1001 -h /app -s /sbin/nologin -G appuser appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user before installing dependencies
USER appuser

# Copy package files (cached layer for dependencies)
COPY --chown=appuser:appuser package.json package-lock.json* ./

# Install dependencies
# Use npm ci for reproducible builds, fallback to npm install if no lock file
RUN if [ -f package-lock.json ]; then npm ci --silent; \
    else npm install --silent; fi

# Copy application code
COPY --chown=appuser:appuser . .

# Expose Vite dev server port
EXPOSE 5173

# Health check for dev server
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5173/ || exit 1

# Start Vite dev server with hot-reload
CMD ["npm", "run", "dev"]
