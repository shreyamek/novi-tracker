#!/usr/bin/env sh
# Start Novi on this computer (http://127.0.0.1:8765). Needs Python 3.11 or newer.
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 was not found. Install Python 3.11 or newer, then run this again." >&2
  exit 1
fi
exec python3 app/run.py "$@"
