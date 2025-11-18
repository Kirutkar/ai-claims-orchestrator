# Frontend Dockerfile - Multi-stage build for Render
# Stage 1: Build
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
# VITE_API_URL must be available at build time (set by Render)
# Render will inject this from backend service URL
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Production
FROM node:18-alpine

WORKDIR /app

# Install serve to run the built app
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/package.json /app/

# Expose port (Render will set PORT env var)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT:-3000}/ || exit 1

# Run the application (support PORT env var from Render)
CMD ["sh", "-c", "serve -s dist -l ${PORT:-3000}"]

