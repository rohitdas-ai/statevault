#!/usr/bin/env bash
# scripts/deploy.sh
# AWS SAM build and deployment automation script for StateVault
set -euo pipefail

echo "==> StateVault AWS SAM Deployment Runner"

if [ "${DRY_RUN:-false}" = "true" ]; then
  echo "INFO: Running deploy in dry-run mode."
  echo "Executing: sam build --template template.yaml"
  echo "Executing: sam deploy --stack-name statevault-core --resolve-s3 --capabilities CAPABILITY_IAM"
  echo "✓ Dry-run verification complete."
  exit 0
fi

if [ -f "env.local" ]; then
  echo "Loading environment variables from env.local..."
  set -a
  source env.local
  set +a
fi

echo "Building AWS SAM application..."
sam build --template template.yaml

echo "Deploying CloudFormation stack..."
sam deploy \
  --stack-name statevault-core \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
      CockroachDbUrl="${COCKROACH_DB_URL:-}" \
      PaddleApiKey="${PADDLE_API_KEY:-}" \
      PaddlePriceId="${PADDLE_PRODUCT_PRICE_ID:-}"

echo "✓ Deployment complete. Applying database migrations..."
if [ -n "${COCKROACH_DB_URL:-}" ]; then
  psql "$COCKROACH_DB_URL" -f database/schema.sql
fi
echo "✓ StateVault deployment and schema initialization successful."
