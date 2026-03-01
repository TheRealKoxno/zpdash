#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/ilyazenno/Desktop/zp_dumper"
OUT_DIR="$ROOT_DIR/dashboard_output"
PORT="${1:-8091}"

cd "$ROOT_DIR"

python3 analyze_dumper.py
python3 build_local_dashboard.py

echo ""
echo "Dashboard ready:"
echo "  http://127.0.0.1:${PORT}/dashboard.html"
echo ""
echo "Press Ctrl+C to stop server."
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$OUT_DIR"
