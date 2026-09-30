#!/usr/bin/env bash
# Vercel build: prerender the site and build the browser SDK, unless a finished build was uploaded with the
# source (a `vercel deploy` from a machine that already ran it). The function serves apps/web/dist.
set -euo pipefail
if [ -f apps/web/dist/index.html ] && [ -f packages/cierto-js/dist/cierto.js ]; then
  echo "using the uploaded build"; exit 0
fi
(cd packages/cierto-js && npm ci --no-audit --no-fund && npm run build)
(cd apps/web && npm ci --no-audit --no-fund && npm run build)
