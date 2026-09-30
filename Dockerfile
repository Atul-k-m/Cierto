# syntax=docker/dockerfile:1.7
# Cierto: one image, one process: the API, the browser SDK bundle and the prerendered site on $PORT.
#
#   docker build -t cierto .
#   docker run --rm -p 8080:8080 -e GEMINI_API_KEY cierto        # then http://localhost:8080
#
# Stage 1 builds the browser SDK and the site with Node; stage 2 is a slim Python runtime that serves them.

# ---- web: packages/cierto-js, then apps/web -------------------------------------------------------
FROM node:22-bookworm-slim AS web
ENV CI=1 NPM_CONFIG_UPDATE_NOTIFIER=false NPM_CONFIG_FUND=false NPM_CONFIG_AUDIT=false
WORKDIR /src
# Lockfiles first, so dependency layers are cached until they change.
COPY packages/cierto-js/package.json packages/cierto-js/package-lock.json packages/cierto-js/
COPY apps/web/package.json apps/web/package-lock.json apps/web/
RUN npm ci --prefix packages/cierto-js && npm ci --prefix apps/web
COPY packages/cierto-js packages/cierto-js
RUN npm run build --prefix packages/cierto-js
# The site's only input outside apps/web: the SDK docs (docs/sdk/*.md, globbed by src/site/docs.ts). Its build is
# tsc, vite (client and SSR), then scripts/prerender.mjs: one index.html per route, 404.html, robots/sitemap/llms
# files and .br/.gz siblings for assets/*.
COPY docs docs
COPY apps/web apps/web
RUN npm run build --prefix apps/web && test -f apps/web/dist/index.html && test -f apps/web/dist/404.html

# ---- runtime ----------------------------------------------------------------------------------------
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080 \
    TRUSTED_PROXY_HOPS=1 \
    FORWARDED_ALLOW_IPS=* \
    LOG_FORMAT=json \
    CIERTO_ENV=dev
WORKDIR /app
RUN groupadd --system --gid 10001 cierto && useradd --system --uid 10001 --gid cierto --home-dir /app cierto

# Dependencies from pyproject.toml (runtime + the redis extra; no Postgres, no dev tools), cached as one layer.
COPY engine/pyproject.toml engine/pyproject.toml
RUN python -c "import tomllib; p = tomllib.load(open('engine/pyproject.toml', 'rb'))['project']; \
print('\n'.join(p['dependencies'] + p['optional-dependencies']['redis']))" > /tmp/requirements.txt \
 && pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# The engine, editable so its paths resolve inside /app (scenarios/, apps/web/dist, packages/cierto-js/dist).
COPY engine/src engine/src
RUN pip install --no-deps -e ./engine && python -m compileall -q engine/src
COPY scenarios scenarios
COPY --from=web /src/packages/cierto-js/dist packages/cierto-js/dist
COPY --from=web /src/apps/web/dist apps/web/dist

USER cierto
EXPOSE 8080
# Docker/Compose only; Cloud Run uses the probes in deploy/cloudrun/service.yaml.
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ.get('PORT', '8080'), timeout=2)"]
CMD ["python", "-m", "wismo", "serve", "--no-build", "--host", "0.0.0.0"]
