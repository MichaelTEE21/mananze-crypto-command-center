#!/usr/bin/env bash
# Render / Docker — bind $PORT; persist SQLite under MCCC_DATA_DIR (/data on Render disk)
set -euo pipefail
PORT="${PORT:-8501}"
export MCCC_DATA_DIR="${MCCC_DATA_DIR:-/data}"
mkdir -p "$MCCC_DATA_DIR" 2>/dev/null || true
exec streamlit run app.py \
  --server.port="$PORT" \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --browser.gatherUsageStats=false
