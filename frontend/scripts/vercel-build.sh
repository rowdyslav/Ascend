#!/bin/sh
set -eu

ASCEND_API_URL="${ASCEND_API_URL:-https://backend-five-swart-37.vercel.app}"

cd "$(dirname "$0")/.."
rm -rf build dist
find . -type d -name __pycache__ -prune -exec rm -rf {} +

python - "$ASCEND_API_URL" <<'PY'
import json
import pathlib
import sys

pathlib.Path("api_config.py").write_text(
    "API_URL = " + json.dumps(sys.argv[1]) + "\n",
    encoding="utf-8",
)
PY

flet publish main.py \
  --assets assets \
  --distpath dist \
  --app-name ASCEND \
  --app-short-name ASCEND \
  --app-description "Трекер здоровья, тренировок и протокола" \
  --route-url-strategy hash