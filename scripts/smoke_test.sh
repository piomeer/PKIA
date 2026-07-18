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
#   4 — JSONL did not grow (no new records ingested)

set -e

JSONL="pkia_project/pkia_storage.jsonl"

echo "=== PKIA Smoke Test ==="

# Record pre-run line count
if [ -f "$JSONL" ]; then
    OLD_COUNT=$(wc -l < "$JSONL")
else
    OLD_COUNT=0
fi
echo "Pre-run JSONL records: $OLD_COUNT"

echo "Running run.py --no-open ..."
python run.py --no-open
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "run.py exited with code $EXIT_CODE"
    exit $EXIT_CODE
fi

# Verify JSONL grew
if [ -f "$JSONL" ]; then
    NEW_COUNT=$(wc -l < "$JSONL")
else
    NEW_COUNT=0
fi
echo "Post-run JSONL records: $NEW_COUNT"
if [ "$NEW_COUNT" -le "$OLD_COUNT" ]; then
    echo "ERROR: No new records in pkia_storage.jsonl"
    exit 4
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
