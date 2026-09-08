#!/bin/sh
set -eu

ASCEND_API_URL="${ASCEND_API_URL:-https://backend-five-swart-37.vercel.app}"
BASE_URL="${BASE_URL:-/Ascend/}"

cd "$(dirname "$0")/.."
rm -rf build dist
find . -type d -name __pycache__ -prune -exec rm -rf {} +

python - "$ASCEND_API_URL" <<'PY'
import json
import pathlib
import sys

pathlib.Path("app/api_config.py").write_text(
    "API_URL = " + json.dumps(sys.argv[1]) + "\n",
    encoding="utf-8",
)
PY

FLET_BIN="$(python -c 'import sysconfig; print(sysconfig.get_path("scripts"))')/flet"
"$FLET_BIN" publish app/main.py \
  --assets assets \
  --distpath ../dist \
  --app-name ASCEND \
  --app-short-name ASCEND \
  --app-description "Трекер здоровья, тренировок и протокола" \
  --base-url "$BASE_URL" \
  --route-url-strategy hash
