#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_TARGET="/tmp/clipforge-venv"

rm -rf "$VENV_TARGET"
python3 -m venv "$VENV_TARGET"
rm -rf "$ROOT_DIR/.venv"
ln -s "$VENV_TARGET" "$ROOT_DIR/.venv"
"$ROOT_DIR/.venv/bin/python" -m pip install --upgrade pip wheel
"$ROOT_DIR/.venv/bin/pip" install -r "$ROOT_DIR/worker/requirements.txt"

echo "Python env ready at $ROOT_DIR/.venv -> $VENV_TARGET"

