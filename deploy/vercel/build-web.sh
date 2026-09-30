#!/usr/bin/env bash
# Vercel "web" service build (runs in apps/web): the browser SDK, then the prerendered site with absolute URLs
# fixed at build time (no server rewrites them on the CDN), then the SDK copied to /sdk so the CDN serves it too.
set -euo pipefail
npm --prefix ../../packages/cierto-js ci --no-audit --no-fund
npm --prefix ../../packages/cierto-js run build
npm run build
mkdir -p dist/sdk
cp ../../packages/cierto-js/dist/*.js ../../packages/cierto-js/dist/*.mjs dist/sdk/
cp dist/sdk/cierto.js dist/sdk/pakka.js   # the old name still loads
