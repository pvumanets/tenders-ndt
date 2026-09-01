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
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts
COPY --from=web /web/dist /app/web-dist

ENV SCOUT_WEB_DIST=/app/web-dist
ENV SCOUT_DOCS_DIR=/data/docs

EXPOSE 8765
ENTRYPOINT ["sh", "/app/scripts/api-entrypoint.sh"]
