#!/bin/sh
set -eu

ASCEND_API_URL="${ASCEND_API_URL:-https://backend-five-swart-37.vercel.app}"
BASE_URL="${BASE_URL:-/Ascend/}"

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

# Pinned runtime deps for Pyodide (must match the flet_web 0.86.5 runtime).
# No flet-cli / flet-desktop here — those are build/dev tools, not web runtime.
cat > "$TMP_DIR/requirements.txt" <<'EOF'
flet==0.86.5
httpx>=0.27,<1.0
matplotlib>=3.9,<4.0
EOF

# Embed the API URL into the staged package (same as before, but inside the
# temp context so the repo stays clean).
python - "$ASCEND_API_URL" "$TMP_DIR" <<'PY'
import json
import pathlib
import sys

pathlib.Path(sys.argv[2], "app", "api_config.py").write_text(
    "API_URL = " + json.dumps(sys.argv[1]) + "\n",
    encoding="utf-8",
)
PY

FLET_BIN="$(python -c 'import sysconfig; print(sysconfig.get_path("scripts"))')/flet"
"$FLET_BIN" publish "$TMP_DIR/main.py" \
  --assets assets \
  --distpath "$(pwd)/dist" \
  --app-name ASCEND \
  --app-short-name ASCEND \
  --app-description "Трекер здоровья, тренировок и протокола" \
  --base-url "$BASE_URL" \
  --route-url-strategy hash

echo "Static bundle ready in $(pwd)/dist"
