# syntax=docker/dockerfile:1
# BuildKit required for cache mounts (DOCKER_BUILDKIT=1 — default in Compose v2).
FROM node:22-alpine AS web
WORKDIR /web
COPY app/web/package.json app/web/package-lock.json ./
RUN npm ci
COPY app/web ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Browsers live in the image at /ms-playwright. Pip wheels + Playwright CDN
# downloads use BuildKit caches so a cold layer rebuild after Docker Desktop
# restart does not re-download ~300MB chromium when the cache volume survived.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/var/cache/ms-playwright \
    pip install --no-cache-dir -r requirements.txt \
    && PLAYWRIGHT_BROWSERS_PATH=/var/cache/ms-playwright playwright install --with-deps chromium \
    && mkdir -p /ms-playwright \
    && cp -a /var/cache/ms-playwright/. /ms-playwright/

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts
COPY --from=web /web/dist /app/web-dist

ENV SCOUT_WEB_DIST=/app/web-dist
ENV SCOUT_DOCS_DIR=/data/docs

EXPOSE 8765
ENTRYPOINT ["sh", "/app/scripts/api-entrypoint.sh"]
