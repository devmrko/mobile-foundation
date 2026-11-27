#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"
uv="${UV_BIN:-uv}"
if ! command -v "$uv" >/dev/null 2>&1; then uv="$project_dir/uvw"; fi
"$uv" sync --locked
"$uv" run --locked ruff check .
"$uv" run --locked ruff format --check .
"$uv" run --locked mypy
"$uv" run --locked pytest
node --test tests/availability.test.mjs
"$uv" build
"$uv" run --locked python scripts/verify_wheel.py --uv "$uv"
