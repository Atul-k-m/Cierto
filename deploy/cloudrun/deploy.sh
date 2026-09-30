#!/usr/bin/env bash
# Deploy Cierto to Cloud Run: build the image with Cloud Build, keep secrets in Secret Manager, apply service.yaml.
#
#   PROJECT_ID=my-project REGION=asia-south1 ./deploy/cloudrun/deploy.sh
#
# Optional environment:
#   SERVICE (cierto)  REPO (cierto)  SITE_URL (https://cierto.example; unset = the request's origin)
#   GEMINI_API_KEY    read from the environment, else prompted (hidden); empty keeps the current secret
#   REDIS_URL         e.g. an Upstash rediss:// URL; read from the environment, else prompted; empty keeps the
#                     current secret. With no Redis at all the service runs with max-instances=1, because
#                     sessions, rate limits and the LLM budget would otherwise be per instance.
# Needs: gcloud (logged in), a project with a billing account. Secrets go to gcloud on stdin, never in argv or logs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-asia-south1}"
SERVICE="${SERVICE:-cierto}"
REPO="${REPO:-cierto}"
SITE_URL="${SITE_URL:-}"
GEMINI_SECRET="${SERVICE}-gemini-api-key"
REDIS_SECRET="${SERVICE}-redis-url"
RUNTIME_SA="${SERVICE}-run@${PROJECT_ID}.iam.gserviceaccount.com"
[ -n "$PROJECT_ID" ] || { echo "Set PROJECT_ID (or: gcloud config set project <id>)" >&2; exit 1; }
gcloud config set project "$PROJECT_ID" >/dev/null

echo "==> APIs"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com \
  secretmanager.googleapis.com iam.googleapis.com

echo "==> Artifact Registry repository ${REPO} (${REGION})"
gcloud artifacts repositories describe "$REPO" --location "$REGION" >/dev/null 2>&1 \
  || gcloud artifacts repositories create "$REPO" --repository-format=docker --location "$REGION" \
       --description "Cierto images"

echo "==> Runtime service account"
gcloud iam service-accounts describe "$RUNTIME_SA" >/dev/null 2>&1 \
  || gcloud iam service-accounts create "${SERVICE}-run" --display-name "Cierto on Cloud Run"

secret_has_version() { gcloud secrets versions list "$1" --filter="state=ENABLED" --limit=1 --format="value(name)" 2>/dev/null | grep -q .; }

put_secret() {   # put_secret NAME VALUE: new version from stdin, only if VALUE is non-empty
  local name="$1" value="$2"
  [ -n "$value" ] || return 0
  gcloud secrets describe "$name" >/dev/null 2>&1 || gcloud secrets create "$name" --replication-policy=automatic
  printf '%s' "$value" | gcloud secrets versions add "$name" --data-file=- >/dev/null
  echo "    stored a new version of ${name}"
}

grant() {   # the runtime service account may read the secret (and nothing else)
  gcloud secrets add-iam-policy-binding "$1" --member="serviceAccount:${RUNTIME_SA}" \
    --role=roles/secretmanager.secretAccessor >/dev/null
}

echo "==> Secrets"
if [ -z "${GEMINI_API_KEY:-}" ] && [ -t 0 ]; then
  read -rsp "    GEMINI_API_KEY (hidden; empty keeps the current secret or runs without a model): " GEMINI_API_KEY; echo
fi
put_secret "$GEMINI_SECRET" "${GEMINI_API_KEY:-}"
unset GEMINI_API_KEY
if [ -z "${REDIS_URL:-}" ] && [ -t 0 ]; then
  read -rsp "    REDIS_URL, e.g. Upstash rediss://… (hidden; empty keeps the current secret or runs without Redis): " REDIS_URL; echo
fi
put_secret "$REDIS_SECRET" "${REDIS_URL:-}"
unset REDIS_URL

HAS_GEMINI=0; secret_has_version "$GEMINI_SECRET" && { HAS_GEMINI=1; grant "$GEMINI_SECRET"; }
HAS_REDIS=0; secret_has_version "$REDIS_SECRET" && { HAS_REDIS=1; grant "$REDIS_SECRET"; }
if [ "$HAS_REDIS" = 1 ]; then
  MAX_INSTANCES=4
else
  MAX_INSTANCES=1
  echo "    no Redis: max-instances=1 (demo sessions, rate limits and the LLM budget live in one instance's memory)"
fi
[ "$HAS_GEMINI" = 1 ] || echo "    no Gemini key: answers and resolutions use the deterministic templates"

echo "==> Build (Cloud Build)"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE}:$(date -u +%Y%m%d-%H%M%S)"
gcloud builds submit "$ROOT" --tag "$IMAGE"

echo "==> Deploy ${SERVICE} (max ${MAX_INSTANCES} instances)"
RENDERED="$(mktemp "${TMPDIR:-/tmp}/cierto-service.XXXXXX")"
trap 'rm -f "$RENDERED"' EXIT
sed -e "s|\${SERVICE}|${SERVICE}|g" -e "s|\${REGION}|${REGION}|g" -e "s|\${PROJECT_ID}|${PROJECT_ID}|g" \
    -e "s|\${IMAGE}|${IMAGE}|g" -e "s|\${MAX_INSTANCES}|${MAX_INSTANCES}|g" -e "s|\${RUNTIME_SA}|${RUNTIME_SA}|g" \
    -e "s|\${GEMINI_SECRET}|${GEMINI_SECRET}|g" -e "s|\${REDIS_SECRET}|${REDIS_SECRET}|g" \
    -e "s|\${SITE_URL}|${SITE_URL%/}|g" \
    "$ROOT/deploy/cloudrun/service.yaml" > "$RENDERED"
[ -n "$SITE_URL" ] || sed -i.bak '/SITE_URL_LINE/d' "$RENDERED"
[ "$HAS_REDIS" = 1 ] || sed -i.bak '/# BEGIN REDIS/,/# END REDIS/d' "$RENDERED"
[ "$HAS_GEMINI" = 1 ] || sed -i.bak '/# BEGIN GEMINI/,/# END GEMINI/d' "$RENDERED"
rm -f "$RENDERED.bak"
gcloud run services replace "$RENDERED" --region "$REGION"

echo "==> Public access"
gcloud run services add-iam-policy-binding "$SERVICE" --region "$REGION" \
  --member=allUsers --role=roles/run.invoker >/dev/null \
  || echo "    could not allow unauthenticated access (an org policy?); the service is private"

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
echo "==> ${URL}"
curl -fsS "${URL}/readyz" && echo
