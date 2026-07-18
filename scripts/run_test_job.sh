#!/usr/bin/env bash
set -euo pipefail

URL="${1:-}"
if [ -z "$URL" ]; then
  echo "Usage: bash scripts/run_test_job.sh <youtube-url>"
  exit 1
fi
curl -s -X POST "http://127.0.0.1:3000/api/jobs" \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"$URL\"}"
