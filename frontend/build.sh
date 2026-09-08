#!/bin/sh
# Local convenience wrapper — builds the static web bundle for GitHub Pages.
# Requires uv on PATH (dependencies are installed into the project venv by uv).
exec sh "$(dirname "$0")/scripts/github-pages-build.sh"
