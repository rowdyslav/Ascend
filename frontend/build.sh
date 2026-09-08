#!/bin/sh
# Local convenience wrapper — builds the static web bundle for GitHub Pages.
# Requires `python` and `flet` (from the project venv) on PATH.
exec sh "$(dirname "$0")/scripts/github-pages-build.sh"
