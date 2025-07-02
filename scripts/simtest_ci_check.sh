#!/bin/bash
set -euo pipefail

echo "🔁 Running policy-violation pack..."
poetry run simtest fuzz --suite policy-violation --quick

echo "🔁 Running long-context pack..."
poetry run simtest fuzz --suite long-context --quick

echo "✅ Local CI dry-run complete. All tests passed."
