# syntax=docker/dockerfile:1
# Thin app image: React dist + app code on top of tenders-ndt-runtime.
# Requires tenders-ndt-runtime:latest (scripts/ensure-runtime-image.py / dev-up / --deploy).
# ARG used by FROM must appear before any FROM.
ARG RUNTIME_IMAGE=tenders-ndt-runtime:latest

FROM node:22-alpine AS web
WORKDIR /web
COPY app/web/package.json app/web/package-lock.json ./
RUN npm ci
COPY app/web ./
RUN npm run build

FROM ${RUNTIME_IMAGE}
WORKDIR /app

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts
COPY --from=web /web/dist /app/web-dist

ENV SCOUT_WEB_DIST=/app/web-dist
ENV SCOUT_DOCS_DIR=/data/docs
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

EXPOSE 8765
ENTRYPOINT ["sh", "/app/scripts/api-entrypoint.sh"]
