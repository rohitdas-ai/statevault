#!/bin/bash
# ccloud CLI cluster health check utility
set -euo pipefail

if [ -z "${COCKROACH_API_KEY:-}" ]; then
  echo "Error: COCKROACH_API_KEY environment variable is not set." >&2
  exit 1
fi

echo "Authenticating ccloud CLI..."
ccloud auth login --token "$COCKROACH_API_KEY"

echo "Retrieving cluster configurations in JSON format..."
ccloud cluster list -o json > clusters.json

CLUSTER_NAME="statevault-db"
echo "Validating connectivity status for: $CLUSTER_NAME"
ccloud cluster describe "$CLUSTER_NAME" -o json > cluster_health.json

echo "Infrastructure verification completed successfully."
