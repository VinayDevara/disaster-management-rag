# ============================================================================
# DisasterRAG Frontend — Multi-stage Dockerfile
# Next.js 16 with standalone output for minimal production image
# Target: Raspberry Pi (ARM64) / any Linux
#
# CHANGES vs original:
#   - Copies .env.local into the builder stage so NEXT_PUBLIC_* vars are
#     baked into the JS bundle without needing --build-arg on every build.
#   - LLM_BACKEND_URL is overridden at runtime to the k8s service name;
#     the 127.0.0.1 value in .env.local is only used for local dev.
# ============================================================================

# ---------------------------------------------------------------------------
# Stage 1: DEPS — install node_modules
# ---------------------------------------------------------------------------
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---------------------------------------------------------------------------
# Stage 2: BUILDER — build the Next.js production bundle
# ---------------------------------------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# .env.local is copied here so Next.js can read NEXT_PUBLIC_* at build time.
# The file already exists at disaster-app-frontend/.env.local on the Pi.
# (Docker build context is ./disaster-app-frontend so the path is just .env.local)
COPY .env.local .env.local

RUN mkdir -p /app/public

# Override only LLM_BACKEND_URL for the build — the rest come from .env.local.
# (LLM_BACKEND_URL is server-side only, so this doesn't affect the client bundle;
#  it's set here just in case any build-time code references it.)
ENV LLM_BACKEND_URL=http://backend.disasterrag.svc.cluster.local:8000

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 3: RUNNER — minimal production image
# ---------------------------------------------------------------------------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
RUN mkdir -p ./public

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# LLM_BACKEND_URL is injected at runtime by Kubernetes (06-frontend.yaml).
# NEXT_PUBLIC_* are already baked into the bundle from .env.local above.

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
