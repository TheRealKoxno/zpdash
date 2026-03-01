#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/ilyazenno/Desktop/zp_dumper"
OUT_DIR="$ROOT_DIR/dashboard_output"
DOCS_DIR="$ROOT_DIR/docs"

cd "$ROOT_DIR"

python3 analyze_dumper.py
python3 build_local_dashboard.py

mkdir -p "$DOCS_DIR"
rm -f "$DOCS_DIR"/*
cp -f "$OUT_DIR"/*.csv "$DOCS_DIR"/
cp -f "$OUT_DIR"/dashboard_report.md "$DOCS_DIR"/
cp -f "$OUT_DIR"/dashboard.html "$DOCS_DIR"/dashboard.html
cp -f "$OUT_DIR"/dashboard.html "$DOCS_DIR"/index.html

echo "GitHub Pages content prepared in: $DOCS_DIR"
echo "Main page: docs/index.html"
