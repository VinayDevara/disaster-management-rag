# ============================================================================
# DisasterRAG Frontend — Multi-stage Dockerfile
# Next.js 16 with standalone output for minimal production image
# Target: Raspberry Pi (ARM64) / any Linux
# ============================================================================

# ---------------------------------------------------------------------------
# Stage 1: DEPS — install node_modules
# ---------------------------------------------------------------------------
FROM node:20-slim AS deps

WORKDIR /app

# Copy package manifests
COPY package.json package-lock.json ./

# Install dependencies (ci = deterministic install from lockfile)
RUN npm ci

# ---------------------------------------------------------------------------
# Stage 2: BUILDER — build the Next.js production bundle
# ---------------------------------------------------------------------------
FROM node:20-slim AS builder

WORKDIR /app

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy all source files
COPY . .

# Ensure public exists so runtime COPY does not fail when repository has no public assets.
RUN mkdir -p /app/public

# ── Build-time args for NEXT_PUBLIC_* variables ────────────────────────
# These are baked into the client JS bundle at build time.
# Pass them with: docker build --build-arg NEXT_PUBLIC_SUPABASE_URL=...
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_GNEWS_API_KEY

ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_GNEWS_API_KEY=$NEXT_PUBLIC_GNEWS_API_KEY

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# Build the standalone production bundle
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 3: RUNNER — minimal production image
# ---------------------------------------------------------------------------
FROM node:20-slim AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# ── Non-root user (UID 1001 to avoid collision with backend UID 1000) ──
RUN groupadd --system --gid 1001 nodejs \
    && useradd --system --uid 1001 --gid 1001 nextjs

# Copy the standalone server, static assets, and public directory
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
# Copy public directory — create it in case it doesn't exist in the source
RUN mkdir -p ./public

# ── Switch to non-root user ───────────────────────────────────────────
USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/', (r) => {if(r.statusCode !== 200) process.exit(1)})" || exit 1

# Start the standalone Next.js server
CMD ["node", "server.js"]
