#!/usr/bin/env bash
# Render / container start — bind host-injected PORT (default 8501).
set -euo pipefail
PORT="${PORT:-8501}"
exec streamlit run app.py \
  --server.port="$PORT" \
  --server.address=0.0.0.0 \
  --server.headless=true
