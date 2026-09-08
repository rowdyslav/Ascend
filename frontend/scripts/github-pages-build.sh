#!/bin/sh
set -eu

BASE_URL="${BASE_URL:-/Ascend/}"
# Strip the leading slash before passing to `flet publish`: MSYS (Git Bash on
# Windows) rewrites a leading-slash argument like `/Ascend/` into a Windows
# path, while `flet publish` normalizes the value itself (strips and re-adds
# slashes), so `Ascend/` and `/Ascend/` produce the same `<base href>`.
BASE_URL_ARG="${BASE_URL#/}"

cd "$(dirname "$0")/.."
rm -rf build dist
find . -type d -name __pycache__ -prune -exec rm -rf {} +

# Stage a minimal publish context in a temp dir. `flet publish` packs the
# *directory of the entry script* into app.tar.gz, so publishing `app/main.py`
# directly would flatten `app/` to the archive root and break every
# `from app.* import ...` at runtime (Pyodide then never starts the UI →
# infinite "Working"). Publishing a tiny shim whose directory is the project
# root keeps the `app` package intact.
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

cp -R app "$TMP_DIR/app"
rm -rf "$TMP_DIR/app/.flet"
cp -R assets "$TMP_DIR/assets"

cat > "$TMP_DIR/main.py" <<'PY'
import flet as ft

from app.main import main

if __name__ == "__main__":
    ft.run(main)
PY

# Pinned runtime deps for Pyodide. IMPORTANT: these MUST stay resolvable by
# the Pyodide runtime bundled with flet 0.86.5 (currently pyodide 314.0.3),
# which ships matplotlib 3.10.8 / numpy 2.4.3 — so matplotlib is NOT pinned to
# the newer native version used by pyproject.toml. A too-new floor here makes
# micropip fail at runtime → the app hangs on the loading spinner.
cat > "$TMP_DIR/requirements.txt" <<'EOF'
flet==0.86.5
httpx>=0.28.1,<1.0
matplotlib>=3.9,<4.0
EOF

uv run --project . flet publish "$TMP_DIR/main.py" \
  --assets assets \
  --distpath "$(pwd)/dist" \
  --app-name ASCEND \
  --app-short-name ASCEND \
  --app-description "Трекер здоровья, тренировок и протокола" \
  --base-url "$BASE_URL_ARG" \
  --route-url-strategy hash

echo "Static bundle ready in $(pwd)/dist"
