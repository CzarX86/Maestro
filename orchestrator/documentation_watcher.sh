#!/usr/bin/env bash
set -euo pipefail

# Watches reports/qa.json for changes and triggers the documentation agent

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
REPORT_FILE="$PROJECT_ROOT/reports/qa.json"
INTERVAL=${DOC_WATCH_INTERVAL:-2}

echo "📝 Documentation watcher started (file: $REPORT_FILE)"

last_mtime=""
while true; do
  if [ -f "$REPORT_FILE" ]; then
    mtime=$(stat -f %m "$REPORT_FILE" 2>/dev/null || stat -c %Y "$REPORT_FILE" 2>/dev/null || echo "0")
    if [ "$mtime" != "$last_mtime" ]; then
      echo "📄 Change detected in qa.json, updating documentation..."
      last_mtime="$mtime"
      # Prefer poetry if available
      if command -v poetry >/dev/null 2>&1; then
        poetry run python -m src.maestro.documentation_agent || echo "⚠️ Documentation agent failed"
      else
        python3 -m src.maestro.documentation_agent || echo "⚠️ Documentation agent failed"
      fi
    fi
  fi
  sleep "$INTERVAL"
done

