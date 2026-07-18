#!/usr/bin/env bash
# PKIA Smoke Test
#
# Usage:
#   bash scripts/smoke_test.sh
#
# Exit codes:
#   0 — All checks passed
#   1 — run.py exited with failure (see output for details)
#   2 — No report file was generated
#   3 — Report file exists but is empty

set -e

echo "=== PKIA Smoke Test ==="
echo "Running run.py --no-open ..."
python run.py --no-open
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "run.py exited with code $EXIT_CODE"
    exit $EXIT_CODE
fi

LATEST=$(ls -t reports/*.md 2>/dev/null | head -1)
if [ -z "$LATEST" ]; then
    echo "ERROR: No report generated"
    exit 2
fi

echo "Latest report: $LATEST"
if [ ! -s "$LATEST" ]; then
    echo "ERROR: Report file is empty"
    exit 3
fi

echo "=== Smoke test passed ==="
